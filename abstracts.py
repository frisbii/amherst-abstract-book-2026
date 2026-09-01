import csv
import os
import re
from operator import itemgetter

from pylatexenc.latexencode import (
    RULE_DICT,
    UnicodeToLatexConversionRule,
    UnicodeToLatexEncoder,
)

""" def sanitize_for_latex(text: str) -> str:
    # single backslashes
    text = text.replace('\\', r'\textbackslash{}')
    
    # standard characters
    text = re.sub(r'([&%$_#{}])', r'\\\1', text)
    
    # ~ and ^ are special
    text = text.replace('~', r'\textasciitilde{}')
    text = text.replace('^', r'\textasciicircum{}')
    
    return text """


fail_count = 0
def generate_texname(discipline: str, title: str) -> str:
    # Clean discipline name
    disc_clean = re.sub(r'[^a-zA-Z0-9]+', '_', discipline).strip('_').lower()
    
    # Grab first 4 words of title and strip special characters
    title_words = re.findall(r'\b[a-zA-Z0-9]+\b', title)[:4]
    title_clean = '_'.join(title_words).lower()
    
    # Fallback if title has no alphanumeric characters
    if not title_clean:
        global fail_count
        title_clean = f"FAILED_TO_NAME_{fail_count}"
        fail_count += 1 

        print(f"generate_texname: failed to form filename from discipline:{discipline} and title:{title}")
        
    return f"{disc_clean}_{title_clean}.tex"



def main():
    INPUT_CSV = "abstractsimport.csv"
    
    # make directory
    os.makedirs("abstracts", exist_ok=True)

    # read csv
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # sort
    rows.sort(key=itemgetter("discipline", "title"))

    # create index file
    index_out = "% Auto-generated index file\n\n"
    lastdisc = ""

    created_count = 0
    raw_count = 0
    skipped_count = 0

    conversion_rule = UnicodeToLatexConversionRule(
        rule_type=RULE_DICT,
        rule={
            0x237A : r"\ensuremath{\alpha}",
            0x200B : r"",
            0x1D6C4 : r"\ensuremath{\boldsymbol{\gamma}}",
            0x1D6FE : r"\ensuremath{\gamma}",
            0x1D6FC : r"\ensuremath{\alpha}",
            0x2A09 : r"\ensuremath{\times}",
            0x2212 : r"\ensuremath{-}",
            0x2014 : r"---"
        }
    )
    u = UnicodeToLatexEncoder(unknown_char_policy="replace", conversion_rules=[conversion_rule, "defaults"])
    uraw = UnicodeToLatexEncoder(unknown_char_policy="replace", conversion_rules=[conversion_rule])

    for row in rows:
        # skip empty rows
        if not row["Timestamp"]:
            continue

        # skip rows that aren't ready
        if row["SUPERFORMATTED"] != "TRUE":
            continue

        # form filename
        if row["latex"]:
            filename = generate_texname(row["discipline"], row["First Name"] + " " + row["Last Name"]) 
        else:
            filename = generate_texname(row["discipline"], row["title"])
        filepath = os.path.join("abstracts", filename)

        # start new discipline in index
        disc_sanitized = row["discipline"].replace("&", "and")
        if disc_sanitized != lastdisc:
            lastdisc = disc_sanitized
            index_out += f"\n\\startdiscipline{{ {lastdisc} }}\n\n"

        # don't reprocess existing abstracts as they could be edited already
        if os.path.exists(filepath):
            skipped_count += 1
        else:
            # form the file contents for this abstract
            if row["latex"]:
                raw_count += 1
                out = uraw.unicode_to_latex(row["latex"])
                out += "\n \\newpage"
            else:
                created_count += 1
                row = {k : u.unicode_to_latex(v) if v is not None else v for k, v in row.items()}
                out = f"""\\makeabstract
    {{
    {row["title"]}
    }}
    {{
    {re.sub(r"\s*\(([^)]+)\)", r"\\textsuperscript{\1}", row["authorship"])}
    }}
    {{
    {rf"\\{'\n'}".join(
        re.sub(r'\(([0-9]+)\)\s*', r'\\textsuperscript{\1} ', line)
        for line in row["affiliations"].split('\n')
        if line
    )}
    }}
    {{
    {row["purpose"]}
    }}
    {{
    {row["methods"]}
    }}
    {{
    {row["results"]}
    }}
    {{
    {row["conclusion"]}
    }}

    \\newpage
    """

            # write to the output file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(out)

        # always update index
        index_out += f"\\input{{abstracts/{filename}}}\n"

    # write index
    with open("abstracts_index.tex", "w", encoding="utf-8") as f:
        f.write(index_out)

    print(f"Done! Created {created_count} new files, added {raw_count} new raw latex submissions, and preserved {skipped_count} existing files.")
    print("Index updated in abstracts_index.tex.")


if __name__ == "__main__":
    main()
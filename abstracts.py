import csv
import os
import re
from operator import itemgetter


def sanitize_for_latex(text: str) -> str:
    # single backslashes
    text = text.replace('\\', r'\textbackslash{}')
    
    # standard characters
    text = re.sub(r'([&%$_#{}])', r'\\\1', text)
    
    # ~ and ^ are special
    text = text.replace('~', r'\textasciitilde{}')
    text = text.replace('^', r'\textasciicircum{}')
    
    return text



def generate_texname(discipline: str, title: str) -> str:
    # Clean discipline name
    disc_clean = re.sub(r'[^a-zA-Z0-9]+', '_', discipline).strip('_').lower()
    
    # Grab first 4 words of title and strip special characters
    title_words = re.findall(r'\b[a-zA-Z0-9]+\b', title)[:4]
    title_clean = '_'.join(title_words).lower()
    
    # Fallback if title has no alphanumeric characters
    if not title_clean:
        title_clean = "abstract"
        
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

    # sanitize submissions
    sanitized_rows = [
        {k: sanitize_for_latex(v) if v is not None else v for k, v in row.items()}
        for row in rows
    ]

    # create index file
    index_out = "% Auto-generated index file\n\n"
    lastdisc = ""

    created_count = 0
    skipped_count = 0

    for row in sanitized_rows:
        # unique ordered file name
        filename = generate_texname(row["discipline"], row["title"])
        filepath = os.path.join("abstracts", filename)

        # start new discipline in index
        if row["discipline"] != lastdisc:
            lastdisc = row["discipline"]
            index_out += f"\n\\startdiscipline{{ {lastdisc} }}\n\n"

        # do not overwrite if file already created
        if os.path.exists(filepath):
            skipped_count += 1
        else:
            created_count += 1
            # use our \makeabstract command
            out = f"""\\makeabstract
{{
{row["title"]}
}}
{{
{re.sub(r"\\s*\\(([^)]+)\\)", r"\\\\textsuperscript{\\1}", row["authorship"])}
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
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(out)

        # always update index
        index_out += f"\\input{{abstracts/{filename}}}\n"

    # write index
    with open("abstracts_index.tex", "w", encoding="utf-8") as f:
        f.write(index_out)

    print(f"Done! Created {created_count} new files, preserved {skipped_count} existing files.")
    print("Index updated in abstracts_index.tex.")



if __name__ == "__main__":
    main()
from typing import List, Tuple
import copy
import os
import fitz  # install with 'pip install pymupdf'
import time




def find_pdf_files(directory):
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def find_directories(directory):
    directories = []
    for root, _, files in os.walk(directory):

        if not root.lower().startswith('.'):
            directories.append(root)
    return directories


def recreate_obsidian_structure(directories, obsidian_vault_path,SRC):
    for d in directories:
        ## change the prefix of source to the osbidian one
        new_path = d.replace(SRC,obsidian_vault_path)

        if not os.path.exists(new_path):
            print(new_path)
            os.makedirs(new_path)

def find_updates(files):
    to_update = []
    now_t = time.time()
    for f in files :
        #ajouter si update dans les dernier 24h
        if now_t - os.path.getmtime(f) < 3600 *25 :
            to_update.append(f)
    return to_update

def get_highlight_type(colors):

    color1 = colors['stroke'][0]

    h_type = -1
    if color1 > 0.97 :
        h_type = 3
    elif color1 >0.47 and color1 < 0.50 :
        h_type = 1
    elif color1 > 0.41 and color1 < 0.43 :
        h_type = 2
    return h_type






def _parse_highlight(annot: fitz.Annot, wordlist: List[Tuple[float, float, float, float, str, int, int, int]]) -> str:
    points = annot.vertices
    quad_count = int(len(points) / 4)
    sentences = []
    for i in range(quad_count):
        # where the highlighted part is
        r = fitz.Quad(points[i * 4 : i * 4 + 4]).rect
        words = [w for w in wordlist if fitz.Rect(w[:4]).intersects(r)]
        sentences.append(" ".join(w[4] for w in words))
    sentence = " ".join(sentences)
    return sentence


def handle_page(page):
    wordlist = page.get_text("words")  # list of words on page
    wordlist.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x

    highlights_type = []
    highlights = []
    text_box = []
    positions = []
    annot = page.first_annot
    while annot:
        if annot.type[0] == 8:
            highlights.append(_parse_highlight(annot, wordlist))
            positions.append(annot.vertices[0])
            highlights_type.append( get_highlight_type(annot.colors))

        if annot.type[0] == 2:
             text_box.append(annot.get_text())


        annot = annot.next
    return highlights, text_box, highlights_type,positions


def create_md(file_path,obsidian_path,src):
    md_path = file_path.replace(src,obsidian_path)
    md_path = md_path.replace(".pdf",".md")
    print(md_path)
    doc = fitz.open(file_path)
    for page in doc:
        positions = []
        highlights = []
        textboxs = []
        highlight_types = []
        highlight , textbox, highlight_type,position  = handle_page(page)
        highlights += highlight
        textboxs += [text.replace("\n", ", ") for text in textbox ]
        highlight_types += highlight_type
        positions += position
        if len(positions) + len(textboxs) == 0:
            continue
        ## sort base on position

        sorted_index = [i[0] for i in sorted(enumerate(positions), key=lambda x: (x[1][1],x[1][0]))]
        sorted_highlights = []
        sorted_type = []
        for i in sorted_index:
            sorted_highlights.append(highlights[i])
            sorted_type.append(highlight_types[i])
            type_prefixes = {1:"# ", 2: "## ", 3 : "" }

        with open(md_path,"a") as f:
            for text,typ in zip(sorted_highlights,sorted_type):
                text = type_prefixes[typ] + text
                f.write(text)
                f.write("\n")
                f.write("\n")
            f.write("<u> NOTES: </u>")
            for text in textboxs:
                f.write(text)
                f.write("\n")
                f.write("\n")
            f.write(f"<center>{page.number}</center>")
            f.write("\n")





def main():
    obsidian_vault_path = "<your obsidian path>"
    SRC = "<your source fodler path>"


    #obsidian_vault_path = "/Users/jacobcote/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/"
    #SRC = "/Users/jacobcote/Library/CloudStorage/OneDrive-UniversitéLaval/Automne_24/"
    os.listdir(SRC)
    os.listdir(obsidian_vault_path)
    # get directories in source directory
    directories = find_directories(SRC)
    # recreate src tree in obsidian
    recreate_obsidian_structure(directories,obsidian_vault_path,SRC)

    # get files in srce and check if updated in last 24 hours
    files = find_pdf_files(SRC)
    to_update = find_updates(files)



    for f in to_update:
        print(f)
        create_md(f,obsidian_vault_path,SRC)







    return None


if __name__ == "__main__":
  main()

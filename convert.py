from datetime import datetime
from PyPDF2 import PdfFileReader, generic
from zipfile import ZipFile
import imghdr
import math
import os
import os.path as p
import sys
import zlib


def get_object_images(x_obj):
    images = []
    for obj_name in x_obj:
        sub_obj = x_obj[obj_name]

        if "/Resources" in sub_obj and "/XObject" in sub_obj["/Resources"]:
            images += get_object_images(sub_obj["/Resources"]["/XObject"].getObject())

        elif sub_obj["/Subtype"] == "/Image":
            zlib_compressed = "/FlateDecode" in sub_obj.get("/Filter", "")
            if zlib_compressed:
                sub_obj._data = zlib.decompress(sub_obj._data)

            images.append(sub_obj._data)

    return images


def get_pdf_images(pdf_fp):
    images = []
    try:
        pdf_in = PdfFileReader(open(pdf_fp, "rb"))
    except:
        return images

    for p_n in range(pdf_in.numPages):

        page = pdf_in.getPage(p_n)

        try:
            page_x_obj = page["/Resources"]["/XObject"].getObject()
        except KeyError:
            continue

        images += get_object_images(page_x_obj)

    return images


def pdf_to_cbz(file_path, out_folder):
    if not p.exists(out_folder):
        os.makedirs(out_folder)

    file_basename = p.splitext(p.basename(file_path))[0]

    with ZipFile(p.join(out_folder, file_basename + ".cbz"), "w") as cbz:
        count = 0
        pdf_images = get_pdf_images(file_path)

        image_name_size = math.log10(len(pdf_images)) + 1
        for image in pdf_images:
            # (mode, size, data) = image
            image_name = (
                str(count).zfill(int(image_name_size))
                + "."
                + imghdr.what(None, h=image)
            )
            cbz.writestr(zinfo_or_arcname=image_name, data=image)
            count += 1


if __name__ == "__main__":
    """
    Utilization:
    pthon convert.py <PDF or folder of PDFs to convert> [<output folder>]
    """

    startTime = datetime.now()
    pdf_count = 0

    out_folder = ""
    if len(sys.argv) > 1:
        in_folder = sys.argv[1]
        if not p.exists(in_folder):
            raise FileNotFoundError("Input file or folder does not exist!")

    if len(sys.argv) > 2:
        out_folder = sys.argv[2]

    # If input is a file, and not a folder
    if p.isfile(in_folder):
        if out_folder == "":
            out_folder = p.dirname(in_folder)
        file_path = p.abspath(in_folder)

        pdf_to_cbz(file_path, out_folder)
        pdf_count += 1
    # If input is a folder, process all PDFs in it
    else:
        if out_folder == "":
            out_folder = in_folder

        for filename in os.listdir(in_folder):
            file_path = p.abspath(p.join(in_folder, filename))
            if p.isfile(file_path) and file_path[-4:] == ".pdf":
                pdf_to_cbz(file_path, out_folder)
                pdf_count += 1

    print(f"Converted {pdf_count} PDF in {datetime.now() - startTime}")

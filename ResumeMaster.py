from pylatex import Document, Command, Section, Package, NewLine, Itemize, Tabular, NoEscape
from pylatex.base_classes import Environment, Options, Arguments
from pylatex.utils import dumps_list as TexList
from pprint import pprint
from dateutil.parser import parse as parsedate
from datetime import datetime
import yaml
from os import path, listdir
import hashlib
import shutil
import os
import argparse
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("datafile", help="the file used as a data source")
parser.add_argument("-l", action="store_true", help="display LaTeX source generated from data")
parser.add_argument("--outdir", default="./", help="output directory")
parser.add_argument("--noinc", action="store_true", help="do not increment revision number")
prog_args = parser.parse_args()

with open(prog_args.datafile) as f:
  portfolio = yaml.safe_load(f)

doc = Document(documentclass='Resume')

with doc.create(Tabular("l")) as ntab:
  ntab.add_row([Command("Huge", Command("textbf", portfolio["name"]))])
  ntab.add_row([Command("Large", portfolio["title"])])

doc.append(Command("hfill"))
with doc.create(Tabular("rl")) as ctab:
  contact_handles = portfolio["contact"]
  for handle in contact_handles:
    ctab.add_row([handle["name"]+": ", TexList([Command("hspace", "5pt"), Command("href", [handle["url"], handle["handle"]])])])

with doc.create(Section("Education", numbering = False)):
  edu = portfolio["education"]
  for school in edu:
    doc.append(Command("par"))
    doc.append(Command("textbf", school["name"]))
    doc.append(Command("hfill"))
    doc.append(school["location"])
    if "subjects" in school:
      doc.append(NewLine())
      subjects = school["subjects"]
      for sdx, subject in enumerate(subjects):
        doc.append(Command("hspace*", "0.25in"))
        if "degree" in subject:
          doc.append(subject["degree"] + " in ")
        doc.append(subject["major"] + " ")
        if "concentration" in subject:
          doc.append("(concentration in {})".format(subject["concentration"]))
        doc.append(Command("hfill"))
        doc.append(subject["date"])
        if "minors" in subject:
          for minor in subject["minors"]:
            doc.append(NewLine())
            doc.append(Command("hspace*", "0.5in"))
            doc.append("Minor in ")
            doc.append(minor)
        if sdx < len(subjects)-1:
          doc.append(NewLine())


with doc.create(Section("Highlights", numbering = False)):
  highlights = portfolio["interests"]
  doc.append(Command("par"))
  with doc.create(Environment(start_arguments=len(highlights))) as env:
    env.latex_name = "multicols"
    for idx, highlight in enumerate(highlights):
        doc.append(Command("textbf", Command("textit", highlight["name"]+":")))
        doc.append(NewLine())
        skills = highlight["skills"]
        for rdx, item in enumerate(skills):
          doc.append(item)
          if rdx < len(skills)-1:
            doc.append(NewLine())
        if idx < len(highlights)-1:
          doc.append(TexList([Command("columnbreak"), Command("par")]))

with doc.create(Section("Skills", numbering = False)):
  skills = portfolio["skills"]
  for idx, category in enumerate(skills):
      skill_list = ""
      for item in category["skills"]:
        skill_list += item + ", "
      doc.append("{}: {}".format(category["name"], skill_list[:-2]))
      if idx < len(skills)-1:
        doc.append(NewLine())

with doc.create(Section("Experience", numbering = False)):
  jobs = portfolio["experience"]
  jobs.sort(reverse = True, key = lambda job: parsedate(job["start"], default=datetime(1, 1, 1, 0, 0)))
  for job in jobs:
    doc.append(Command("par"))
    if "title" in job:
      if "type" in job:
        doc.append(Command("textbf", "{} ({})".format(job["title"],job["type"])))
      else:
        doc.append(Command("textbf", job["title"]))

    doc.append(Command("hfill"))
    datestr = job["start"]
    if "end" in job:
      datestr = "{} - {}".format(datestr, job["end"])
    doc.append(datestr)

    if "employer" in job:
      doc.append(NewLine())
      doc.append(job["employer"])

    if "tasks" in job:
      with doc.create(Itemize()) as itemize:
        for task in job["tasks"]:
          itemize.add_item(task)
    elif "projects" in job:
      with doc.create(Itemize()) as itemize:
        for project in job["projects"]:
          itemize.add_item(project["brief"])

with doc.create(Section("Projects", numbering = False)):
  projects = portfolio["projects"]
  for project in projects:
    doc.append(Command("par"))
    doc.append(Command('textbf', "{} - ".format(project["name"])))
    doc.append(project["description"])

doctitle = 'Resume of {}'.format(portfolio["name"])
docauthor = portfolio["name"]
metadata = NoEscape(Options(
    pdftitle=doctitle,
    pdfauthor=docauthor,
    pdfcreator="PyResume with XeLaTeX",
).dumps()[1:-1])

doc.preamble.append(Command('title', doctitle))
doc.preamble.append(Command('author', docauthor))
doc.preamble.append(Command('date', Command('today')))
doc.preamble.append(Command('hypersetup', metadata))
doc.packages.clear()

if prog_args.l:
  print(doc.dumps())

out_dir = path.realpath(prog_args.outdir)
prog_path = path.dirname(path.realpath(__file__))
latex_path = path.join(prog_path, "latex")


# Determine final location of output file
file_name = path.join(out_dir, "{} ({})".format(doctitle, datetime.today().strftime("%b, %Y")))
if not path.exists(out_dir):
  os.mkdir(out_dir)
count = 0
next_name = "{} R{}".format(file_name, count)
out_name = next_name
while path.exists(next_name + ".pdf"):
  out_name = next_name
  count += 1
  next_name = "{} R{}".format(file_name, count)
if not prog_args.noinc:
  out_name = next_name
out_path = out_name + ".pdf"

with tempfile.TemporaryDirectory() as build_directory:
  build_path = path.join(build_directory, "build_doc")
  build_result = build_path + ".pdf"

  shutil.copytree(latex_path, build_directory, dirs_exist_ok=True)
  doc.generate_pdf(build_path, compiler="xelatex")
  shutil.move(build_result, out_path)

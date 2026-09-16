I need you to do a "monumental" tasks : a full repo reorganization.

In this session you have access to two repository :
- `cv_claude` : contain a new cv I'm working on, written in LaTeX.
- `jesus-333.github.io` : A website CV, based on the famous `al-folio` template

# Your Goal

Merge the two repo in a single one. More precisely you need to migrate the content of `cv_claude` inside `jesus-333.github.io`.

Bear in mind. I'm not a web developed so some of my design choices could be wrong.
In that case you have to point me out the errors and the other options available.

# Repo structure

For the new repo I'm thinking of using this structure :
```
cv_tex/
    ...
cv_web/
    ...
common_material/
    ...
README.md
other_files
```

`cv_tex` should contain all the material in the old `cv_claude`.

`cv_web` should contain most of the material in `jesus-333.github.io`. More precisely I want inside this folder all the material related to website itself (`html`, `json` etc etc).
Things that are not strictly related to the website (e.g. agent config, github workflow should stay in the repository root).

The folder `common_material` should contain material that can be useful to both project (e.g. bibliography and profile picture).

`other_files` is whatever files should stay in the repository root.

Since all the repo structure will be modified you need to update also all the file related to deployment, github action etc. I do not have the background to do it, so I have to trust you for this process.

# Notes on the tex cv

I want all the file inside `cv_tex` to be a standalone project that I could also import on overleaf. 
I am thinking of handling the matter in the following way.
- Keep the `cv_claude` for synchronization between Github/overleaf. 
- Using a github action to push update from the `jesus-333.github.io` repo to the `cv_claude`. This action should be triggered only if some change in the `tex` files is detected.

Then I want some python scripts that basically take the info from the website and convert them in the proper `tex` file to use inside the cv.
The scripts must not run automatically. They must be run manually in (ideally) two ways 
- Locally from my machine with the python command (this is mandatory)
- On Github through an action that I can trigger manually (this second method is optional, and if it cannot be implemented (or is too complicated), it does not matter.)

I also like to have an optional script/workflow to trigger manually on my pc that compile the LaTeX file and produce the PDF.
This script should place the `pdf` (or a copy of it) inside the folder `assets/pdf/` (or its corresponding folder after the reorganization).
It is the folder that contains the PDF that user can download from the website. Basically, when I compile the cv I want that also the PDF linked on the website to be updated.

# General clean up

If there are assets that are not useful you could remove them.

Regarding the instructions file of `al-folio` you can keep them

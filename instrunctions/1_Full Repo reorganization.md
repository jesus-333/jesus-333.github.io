I need you to do a "monumental" tasks : a repo reorganization.

In this session you have access to two repository :
- `cv_claude` : contain a new cv I'm working on, written in LaTeX.
- `jesus-333.github.io` : A website CV, based on the famous `al-folio` template

# Your Goal

Merge the two repo in a single one. More precisely you need to migrate the content of `cv_claude` inside `jesus-333.github.io`.

Bear in mind. I'm not a web developed so some of my design choices could be wrong.
In that case you have to point me out the errors and the other options available.

# Repo structure,"philosophy" and various details

I want you to keep the structure of the actual `al-folio` template, but you need to add some stuff. 
- A folder called `cv_tex` where all the files related to the LaTeX will be stored.
- A `common_material` folder for material used for both project (if you think this is a bad design decision explain me why).
If this entails changes to deployment files, GitHub Actions, etc., you will have to handle that yourself, as I don't have the background for it. I need to be able to trust you on this.


I want all the file inside `cv_tex` to be a standalone project that I could also import on overleaf. 
I am thinking of handling the matter in the following way.
- Keep the `cv_claude` for synchronization between Github/overleaf. 
- Using a github action to push update from the `jesus-333.github.io` repo to the `cv_claude`. This action should be triggered only if some change in the `tex` files is detected.

I also like to have an optional script/workflow to trigger manually on my pc that compile the LaTeX file and produce the PDF.
This script should place the `pdf` (or a copy of it) inside the folder `assets/pdf/` (or its corresponding folder after the reorganization).
It is the folder that contains the PDF that user can download from the website. Basically, when I compile the cv I want that also the PDF linked on the website to be updated.

Then I want a python script that basically take the info from the website and convert them in the proper `tex` file to use inside the cv (or more than one if help keeping everyhing clear and organized)
The script(s) must not run automatically. It(s) must be run manually in (ideally) two ways 
- Locally from my machine with the python command (this is mandatory)
- On Github through an action that I can trigger manually (this second method is optional, and if it cannot be implemented (or is too complicated), it does not matter.)

I see that the template take all the info from the `json` resume. I think you could take its filed and migrate them to the `tex` files.

There should also be a `toml` file with the same data of the `json` resume. I feel more comfortable editing `toml` files than `json` files.
Related to this `toml` file there should also be a simple python script that produce the `json` version from the `toml` version.

I see that there is also a project section in the website. Prepare a small python script that scrap each one of the project for the name and a brief description. The description should be the first paragraph inside the corresponding `md` file.
(At the moment the project are still the one included in the original template... When I add mine I will ensure they have the appropriate structure)

# Other notes

If there are assets that are not useful you could remove them.

If you need more informations or instructions let me know.

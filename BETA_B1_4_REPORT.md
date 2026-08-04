# PP-AIPP v3.0.0-beta.5 — Sprint Beta B1.4

## Delivered

- Build Book writes the production DOCX to the visible project `build` folder.
- The console prints the complete built-book path and controlled-content coverage.
- The completion dialog offers **Open Book** and **Open Folder** actions.
- The Gold Master parser recognises `Method`, `Directions`, `Instructions`, and
  `Meal Prep` headings in paragraphs, inline headings, numbered headings, and
  labelled table rows.
- Missing Method/Meal Prep content remains explicitly identified as unavailable;
  PP-AIPP does not mislabel invented editorial copy as controlled-source content.
- Windows build workflow artifact is named `PP-AIPP-Windows-beta.5-B1.4`.

## Acceptance flow

1. Open Project
2. Import Gold Master
3. Validate
4. Build Book
5. Select **Open Book** or **Open Folder**

The expected output is:

`<project>/build/Project_Physique_30_Days_Fat_Loss_Built.docx`

## Verification

- Python source and test modules compile successfully.
- B1.4 integration smoke test passed.
- The smoke test confirmed two controlled Method steps, controlled Meal Prep,
  database persistence, DOCX generation, and output inside `build`.
- The bundled 80-recipe alpha preview is a previously generated layout artifact,
  not a controlled Gold Master input; it must not be used as parser acceptance data.

# Install and test Beta B2.7

1. Copy every file from this source package into `C:\BLICIU\PP-AIPP` and replace the old files.
2. In GitHub Desktop commit the changes to `main`, then click **Push origin**.
3. In GitHub Actions wait for both green B2.7 workflows.
4. Download artifact `PP-AIPP-Windows-beta.6-B2.7` and extract it.
5. Run `PP-AIPP.exe`, open the existing project and make sure its book was built.
6. Click **Generate AI Photos**.
7. Paste an OpenAI API key, choose batch size and quality, then confirm the billed run.
8. When generation finishes, click **Export** to rebuild the PDF package with the new photos.

The campaign skips existing images and can be run again after an interruption. The key
is held only in application memory for the current run.

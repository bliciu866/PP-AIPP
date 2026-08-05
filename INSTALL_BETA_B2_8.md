# Install Beta B2.8 on Windows

1. Copy this source tree into the local PP-AIPP repository and replace matching files.
2. Commit with the message from `COMMIT_MESSAGE.txt`, then push `main`.
3. Wait for both GitHub Actions workflows to finish with green checks.
4. Download the `PP-AIPP-Windows-beta.6-B2.8` artifact and extract it fully.
5. Run `SETUP_LOCAL_AI.bat` once and wait for installation to finish.
6. Run `PP-AIPP.exe`.
7. Open the project, click `Generate AI Photos`, and select `Local Free AI`.
8. Test with batch size `1` and quality `Low`, then run larger resumable batches.

Do not run the EXE or setup directly inside a ZIP archive. Always extract the package
first. The first photo generation downloads the model and can take additional time.

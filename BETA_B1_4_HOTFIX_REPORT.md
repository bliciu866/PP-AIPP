# Beta B1.4 CI Hotfix

Updates the desktop-state test to expect the B1.4 production output directory
`build` instead of the legacy B1.3 directory `exports`.

The application implementation was already correct; only the stale assertion
blocked Quality Gate and the Windows EXE workflow.

The runtime version is also aligned with the package version
`3.0.0b5.post14`, satisfying the release-version consistency gate.

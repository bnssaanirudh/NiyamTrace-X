# Final review pack

- [Run, navigate and speak](RUN_NAVIGATE_AND_SPEAK.md): startup, navigation, core actions and talking points.
- [All role demonstrations](ALL_ROLES_DEMONSTRATION.md): token generation, every role, requests, observations and further demonstrations.
- [Five-minute demonstration](FIVE_MINUTE_LIVE_DEMONSTRATION.md): timed actions and words to say.
- [Fifteen-minute project and paper pitch](FINAL_REVIEW_15_MINUTE_PITCH.md): presentation script with experimental findings and limits.
- [100 faculty questions](FACULTY_100_QUESTIONS.md): suggested answers covering architecture, roles, controls, experiments, results and limitations.
- [Workspace quickstart](WORKSPACE_QUICKSTART.md): setup and verification commands.

The recordings are at `niyamtrace/artifacts/recordings/NiyamTrace_6_minute_demo.mp4` in this branch.

**Runtime version:** These instructions describe the current local workspace at `C:\Users\aniru\Downloads\NYAMTRACE\niyamtrace`. At publication, this GitHub archive branch does not contain the newer local `scripts/start_workspace.py` or its full workspace implementation. Downloading this branch alone will not recreate the demonstrated runtime. The review files and video were uploaded separately; the local source changes need to be reviewed and published before these commands can run from a fresh clone.

**Credentials:** The launcher generates six temporary tokens for the current local session. Their actual values must stay private. An existing background launch may have them in `.workspace-runtime/launcher-current.log`; newly launched services print fresh values to that terminal. The launcher signing secret changes on restart. The local `.workspace-runtime/demo-identities.log` is a snapshot, not a source of valid new credentials, and may expire or become stale. No token values are published in this review pack.

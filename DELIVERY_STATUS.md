# Episode 001 delivery status

- Full MP4 rendered and decoded successfully: 60.000 seconds, 1,800 frames,
  1080×1920, 30 fps, H.264/yuv420p, stereo AAC, 38,808,056 bytes.
- A five-second preview was rendered and checked before full rendering.
- Visual contact sheet checked for all five scenes and the starting shot.
- All audio is locally synthesized, with no speech or music.
- Rendering uses a 120 Hz hybrid constrained simulation / choreographed animation.
- Source code, JSON configuration, verification utility, release publisher, and
  local Git commit are provided. Large MP4 files are excluded from Git and are
  intended to be GitHub Release assets.
- Connected GitHub account: shirura1-a11y. Accessible-repository list and exact
  repository lookup did not find `marble-survival` (lookup returned 404).
- Repository creation was attempted using `gh repo create ... --public`.
  The environment HTTP proxy denied the CONNECT tunnel to api.github.com with
  HTTP 403. `gh` authentication status could not be reliably determined through
  this blocked API path. Available GitHub connector actions do not include
  repository creation or Release asset upload.
- Consequently no remote repository, remote push, Release, or GitHub download URL
  was created. No claim of successful publication is made.
- Files are retained in the cloud workspace output folder. The chat client's
  requested `/codex/browser/.../output` export mount is absent in this executor;
  creating it failed because the executor root filesystem is read-only.
- No paid APIs or services were used.

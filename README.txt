LOCAL MIDI - FREE REMOTE APPLE SILICON BUILD

EASIEST SETUP ON YOUR MAC

Double-click StartFreeBuild.command in this folder. It downloads a prebuilt
GitHub CLI 2.100.0 for your Mac, verifies its pinned SHA-256, asks you to sign in
to GitHub in your browser, creates a public repository, uploads only the build
files, starts the free Apple Silicon build, and downloads the finished installer
into this folder's Installers directory. Keep Terminal open while it works.
Homebrew and a Go compiler are not needed. The CLI stays in this folder's
.tools directory; it does not replace any system-wide GitHub CLI installation.
CLI 2.100.0 uses Go 1.26, which supports macOS 12. Later Go 1.27 builds require
macOS 13. The pinned archive hashes come from GitHub's official release assets:
https://github.com/cli/cli/releases/expanded_assets/v2.100.0
Your GitHub plugin login is separate from this command-line login.

The launcher uploads through GitHub's API, with progress for each file and a
120-second timeout for each request. It reuses files already uploaded and
resumes interrupted uploads. Once the build starts, it opens the GitHub Actions
run in your browser. Yellow means queued/running, green means successful, and
red means failed. No build starts until all source files are confirmed uploaded.
If an older launcher is stuck after "Writing objects", press Control+C and
reopen this updated launcher. It will reuse the repository already created.

The remote build applies a reviewed correction after verifying/extracting the
original ZIP: macOS 12.3 is the installer and native deployment minimum because
the bundled SciPy 1.16.1 arm64 binary requires 12.3 despite its macOS 12.0 wheel
tag. The binary compatibility audit remains enabled. macOS 12.6.2 is supported.
The original downloaded ZIP and the existing Intel installer are untouched.
This correction is visible in scripts/prepare_build_kit.py and checked before
compiling. Dependencies and models retain the kit's existing versions/hashes.
If another build fails, the launcher downloads its failed-step log into this
folder automatically so the assistant can inspect it without another log step.

This launcher publishes the build-kit SOURCE in a public repository, as you
approved. It leaves the built installer in a draft release. It does not change
your account's billing settings or use a paid runner. Its repository check and
the workflow's public-only condition prevent private-repository compute use.

The launcher stores the repository name and run number locally. It stores no
passwords or tokens in this folder. GitHub CLI manages its own authentication.
Those local state files, the launcher, its tools, and downloaded installers are excluded
from the upload. Reopening the launcher reuses its repository and starts a new
build. Download failures can be recovered from the repository's draft release.

MANUAL SETUP

This folder is ready to upload to a GitHub repository. It contains the original
build-kit ZIP, a manually started GitHub Actions workflow, and an installer
verification script. No account credentials or local build output are included.

The workflow is intentionally restricted to PUBLIC repositories. GitHub's
standard macos-15 Apple Silicon runner is free for public repositories. In a
private repository the build job is skipped, preventing paid compute usage.
Making this repository public exposes the build-kit source code to everyone.
Only do that if you want the source to be public.

Once the repository is public and these files are on its default branch:
1. Open the repository's Actions tab.
2. Select "Build Apple Silicon installer for free".
3. Choose "Run workflow".
4. After it succeeds, open the run's summary and follow its draft-release link.
5. Download Local MIDI-0.2.0-macOS-arm64-unsigned.pkg.

The package installs the app, VST3, Python runtime and models at the paths set
by the original build kit. It is unsigned. No signing certificate is needed
to compile this development installer. App and DAW validation still need to
be completed on Apple Silicon before distributing a release.

The finished installer is attached to a DRAFT RELEASE rather than Actions
artifact storage. The workflow does not publish the release. Release assets
must each be below 2 GiB. It uploads the package, JSON build report and checksum.

The build runs only when explicitly started. It is limited to one concurrent
run and a 180-minute timeout. It does not use paid larger runners or Actions
artifact/cache storage.

The original ZIP is verified against this SHA-256 before extraction:
26dacc3410dc44acd35c099c06878335d2bba094ca8285cedba95034e21eaf12

GitHub references:
https://docs.github.com/en/billing/concepts/product-billing/github-actions
https://docs.github.com/en/actions/reference/runners/github-hosted-runners
https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases

The launcher reports success after the remote build completes and the downloaded
installer passes its checksum and architecture checks. Preparing these files
does not establish app or DAW validation on a target Mac.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-03-18

### Added
- Initial release of OpenClaw Android Scheduler
- Python daemon template for cron-like scheduling on Android/Termux/PRoot
- Automatic timezone handling (Beijing Time UTC+8)
- State tracking to prevent duplicate executions
- Support for configurable time windows
- Support for weekday-based scheduling
- Daemon management commands (start/stop/restart/once)
- Comprehensive documentation (README, SKILL.md)
- MIT License

### Features
- Platform detection for Android/Termux/PRoot environments
- Background process management via PID files
- JSON-based state persistence
- Detailed logging with dual timezone display
- Configurable task scheduling via Python dictionary

[Unreleased]: https://github.com/kirk-haodong/openclaw-android-scheduler/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/kirk-haodong/openclaw-android-scheduler/releases/tag/v1.0.0

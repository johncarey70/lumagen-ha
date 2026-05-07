## v0.1.0 - Initial release

> **Important:** This version requires Lumagen firmware **030326 or later**.
>
> This version does **not** use Lumagen command delimiters. Configure the Lumagen Radiance Pro with:
>
> ```text
> MENU -> Other -> I/O Setup -> RS-232 Setup -> Echo -> On
> MENU -> Other -> I/O Setup -> RS-232 Setup -> Delimiters -> Off
> MENU -> Other -> I/O Setup -> RS-232 Setup -> Report mode changes -> Fullv5
> ```

### Added

- Initial Lumagen Radiance Pro Home Assistant integration.
- UI-based configuration flow.
- TCP serial and USB serial connection support.
- Media player entity with power and source selection.
- Remote entity with Lumagen command support.
- Button entities for common controls.
- Switch entities for supported toggle controls.
- Sensor entities for Lumagen status and diagnostics.
- Home Assistant actions for input labels and OSD messages.
- HACS custom repository support.

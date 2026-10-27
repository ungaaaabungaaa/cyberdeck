# Manual target setup

Nothing was installed or enabled by this generator. These templates target a Raspberry Pi OS 64-bit desktop with labwc and Chromium. Hardware boot and kiosk operation are not yet verified.

1. Set up Raspberry Pi OS with the official Imager. Choose your own credentials. Do not put credentials in this repository.
2. Place the checked-out project at `/home/deck/cyberdeck`. Confirm Python 3.11+ and Chromium are installed on the target. Run `python3 -m cyberdeck status --live` there. Missing sensors stay null.
3. Review `cyberdeck.service`. Copy it to the target user's `~/.config/systemd/user/`, then run `systemctl --user daemon-reload` and `systemctl --user enable --now cyberdeck.service` as that user. Check `systemctl --user status cyberdeck.service`.
4. Open http://127.0.0.1:8794/ on the target. Verify the LIVE label and each reading against the OS before using the display.
5. For optional kiosk startup, back up `~/.config/labwc/autostart` and append the reviewed fragment. Do not replace its existing content. Log out/in and test. The service starts at user login, not as an installed system image.
6. Roll back with `systemctl --user disable --now cyberdeck.service`, remove only this service and the added autostart line, and restore the saved configuration if needed. No data partition is changed.

Official guide: https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/

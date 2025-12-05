# ONS Driver

This is a python library to start OBS Studio and control it.

## Using the action

We provide an action for GitHub workflows.
```yaml
      - name: 'Setup onsdriver'
        uses: noris-plugin-for-obs/onsdriver@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          obs-plugins: |
            ${{ runner.os == 'Linux' ? '' : 'build/' }}
      - name: 'Test with onsdriver'
        run: |
          python -m unittest discover test-onsdriver/
```

### Environment variables

| Name | Purpose |
| ---- | ------- |
| `HOME` | Home directory to set the configuration directory for Linux and macOS. |
| `AppData` | AppData directory to set the configuration directory for Windows. |
| `XDG_CONFIG_HOME` | Optionally overwrites the configuration directory derived from `HOME` directory for Linux. |
| `OBS_EXEC` | Optionally configures path to the OBS Studio executable file. |
| `GITHUB_TOKEN` | Optionally uses this token to download plugin from GitHub. |
| `ONSDRIVER_LOGS` | Optionally sets location to move log files to. |

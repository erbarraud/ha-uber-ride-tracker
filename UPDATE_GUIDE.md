# Update Guide for Uber Ride Tracker

This guide explains how updates work and how to ensure the best user experience.

## 🔄 Automatic Update System

### For HACS Users (Recommended)

HACS provides the best update experience:

1. **Automatic Notifications**: You'll see update badges in the HACS panel
2. **One-Click Updates**: Click "Update" and HACS handles everything
3. **Changelog Preview**: See what's new before updating
4. **Rollback Option**: Easily downgrade if needed

### For Manual Installation Users

The integration includes an Update entity that:
- Checks for new versions every 12 hours
- Shows in Settings → Updates alongside HA core updates
- Displays release notes
- Provides update notification

## 📊 Update Entity

The integration provides `update.uber_ride_tracker_update` entity with:
- Current version
- Latest available version
- Release notes summary
- Update availability status

### Dashboard Card Example
```yaml
type: custom:mushroom-update-card
entity: update.uber_ride_tracker_update
show_buttons_control: true
```

## 🔧 Configuration Migration

The integration automatically handles configuration updates:

### What Gets Migrated
- OAuth tokens and credentials
- Custom settings and preferences
- Entity configurations
- Device associations

### Migration Process
1. **Backup**: Config backed up before migration
2. **Update**: Automatic conversion to new format
3. **Validation**: Compatibility check
4. **Rollback**: Automatic rollback if migration fails

## 📝 Breaking Changes Handling

### Notification System
When breaking changes occur:
1. Persistent notification appears in HA
2. Update entity shows warning
3. Changelog details required actions

### Example Automation
```yaml
automation:
  - alias: "Uber Tracker Update Available"
    trigger:
      - platform: state
        entity_id: update.uber_ride_tracker_update
        attribute: latest_version
    condition:
      - condition: template
        value_template: >
          {{ state_attr('update.uber_ride_tracker_update', 'latest_version') != 
             state_attr('update.uber_ride_tracker_update', 'installed_version') }}
    action:
      - service: notify.mobile_app
        data:
          title: "Uber Tracker Update Available"
          message: >
            Version {{ state_attr('update.uber_ride_tracker_update', 'latest_version') }}
            is available. Current: {{ state_attr('update.uber_ride_tracker_update', 'installed_version') }}
          data:
            url: "{{ state_attr('update.uber_ride_tracker_update', 'release_url') }}"
```

## 🚀 Best Practices for Updates

### Before Updating
1. **Read Release Notes**: Check CHANGELOG.md for breaking changes
2. **Backup Config**: HA automatically creates backups, but manual backup is recommended
3. **Check Automations**: Verify entity names haven't changed

### During Update
1. **HACS Method**: Use HACS interface for smoothest experience
2. **Manual Method**: Download release, extract, restart HA
3. **Docker Users**: Rebuild container after update

### After Update
1. **Verify Entities**: Check all entities are working
2. **Test Automations**: Ensure automations still trigger
3. **Review Logs**: Check for any error messages

## 🔄 Version Numbering

We follow semantic versioning (MAJOR.MINOR.PATCH):

| Version Type | When Used | User Action Required |
|-------------|-----------|---------------------|
| Patch (0.0.X) | Bug fixes | None - Auto-update safe |
| Minor (0.X.0) | New features | None - Review new features |
| Major (X.0.0) | Breaking changes | May need reconfiguration |

## 🛡️ Rollback Procedure

### If Update Causes Issues

#### HACS Rollback
1. HACS → Integrations → Uber Ride Tracker
2. Three dots menu → Redownload
3. Select previous version
4. Restart Home Assistant

#### Manual Rollback
1. Download previous release from GitHub
2. Delete current integration folder
3. Extract previous version
4. Restart Home Assistant

#### Config Restoration
```yaml
# The integration automatically keeps backups
# Located in: .storage/uber_ride_tracker_backups.json
```

## 🔔 Update Notifications

### Built-in Notifications
- Update entity in Settings → Updates
- Optional persistent notifications
- Device tracker for update status

### Custom Notification Options
```yaml
# Discord/Slack/Email notification on update
automation:
  - alias: "Notify on Uber Tracker Update"
    trigger:
      - platform: state
        entity_id: update.uber_ride_tracker_update
        attribute: latest_version
    action:
      - service: notify.discord  # or notify.email, notify.slack
        data:
          message: >
            🚗 Uber Ride Tracker Update Available!
            New Version: {{ state_attr('update.uber_ride_tracker_update', 'latest_version') }}
            Release Notes: {{ state_attr('update.uber_ride_tracker_update', 'release_summary') }}
```

## 🤖 Automated Updates

### Enable Auto-Updates (HACS)
1. HACS → Integrations → Uber Ride Tracker
2. Three dots → Enable automatic updates
3. Updates install automatically overnight

### Scheduled Update Check
```yaml
automation:
  - alias: "Check Uber Tracker Updates Daily"
    trigger:
      - platform: time
        at: "03:00:00"
    action:
      - service: homeassistant.update_entity
        entity_id: update.uber_ride_tracker_update
```

## 📚 Resources

- [Changelog](CHANGELOG.md) - Detailed version history
- [GitHub Releases](https://github.com/yourusername/ha-uber-ride-tracker/releases) - Download specific versions
- [Issue Tracker](https://github.com/yourusername/ha-uber-ride-tracker/issues) - Report update issues
- [Discussions](https://github.com/yourusername/ha-uber-ride-tracker/discussions) - Get help with updates
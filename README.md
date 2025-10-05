# Gmail OAuth Client JSON Generator - Playwright Edition

A modern, robust automation tool for generating Gmail OAuth client JSON files using Playwright. This tool automates the complete process of creating Google Cloud projects, enabling Gmail API, setting up OAuth consent screens, and downloading credential files.

## 🚀 Features

- **Modern Playwright Automation**: Replaces Selenium with faster, more reliable Playwright
- **Anti-Detection Technology**: Advanced stealth mode and human-like behavior simulation
- **Comprehensive Error Handling**: Robust retry mechanisms and detailed error reporting
- **Batch Processing**: Process multiple accounts simultaneously with concurrency control
- **Enhanced GUI**: Modern tkinter interface with real-time progress tracking
- **Centralized Configuration**: Easy-to-manage settings and preferences
- **Detailed Logging**: Comprehensive logging with multiple output formats
- **Report Generation**: Detailed success/failure reports with statistics

## 📋 Requirements

- Python 3.8 or higher
- Windows 10/11 (tested platform)
- Internet connection
- Valid Gmail accounts for OAuth setup

## 🛠️ Installation

1. **Clone or download the project**:
   ```bash
   cd playwright_gmail_oauth
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

## 🎯 Quick Start

### Single Account Processing

1. Run the application:
   ```bash
   python main.py
   ```

2. Go to the "Single Account" tab
3. Enter your Gmail email and password
4. Click "Generate OAuth JSON"
5. The tool will automatically:
   - Login to Google Cloud Console
   - Create a new project (or select existing)
   - Enable Gmail API
   - Setup OAuth consent screen
   - Create OAuth credentials
   - Download and organize the JSON file

### Batch Processing

1. Prepare a CSV or Excel file with columns:
   - `email`: Gmail address
   - `password`: Account password

2. Go to the "Batch Processing" tab
3. Select your accounts file
4. Click "Load Accounts" to preview
5. Click "Start Batch Processing"

## 📁 Project Structure

```
playwright_gmail_oauth/
├── main.py                     # Main GUI application
├── playwright_automation.py    # Core Playwright automation engine
├── google_cloud_automation.py  # Google Cloud Console automation
├── oauth_credentials.py        # OAuth credentials management
├── config.py                   # Configuration management
├── error_handler.py            # Error handling and logging
├── requirements.txt            # Python dependencies
├── test_implementation.py      # Test suite
├── README.md                   # This file
├── config/
│   └── settings.json          # Configuration file (auto-created)
├── output/
│   ├── json_files/            # Generated OAuth JSON files
│   ├── reports/               # Processing reports
│   ├── screenshots/           # Debug screenshots
│   ├── downloads/             # Browser downloads
│   └── logs/                  # Application logs
└── .env                       # Environment variables (optional)
```

## ⚙️ Configuration

### GUI Settings

Access settings through the "Settings" tab:

- **Browser Settings**:
  - Headless Mode: Run browser in background
  - Stealth Mode: Enable anti-detection features

- **Automation Settings**:
  - Retry Attempts: Number of retries for failed operations
  - Concurrent Limit: Maximum parallel processes for batch mode

### Advanced Configuration

Edit `config/settings.json` for advanced options:

```json
{
  "browser": {
    "headless": false,
    "timeout": 30000,
    "user_agent": "custom-user-agent"
  },
  "automation": {
    "stealth_mode": true,
    "max_retries": 3,
    "concurrent_limit": 2,
    "human_delay_min": 1.0,
    "human_delay_max": 3.0
  },
  "paths": {
    "output_dir": "output/json_files",
    "reports_dir": "output/reports",
    "screenshots_dir": "output/screenshots"
  }
}
```

## 🔧 Testing

Run the test suite to verify installation:

```bash
python test_implementation.py
```

This will test:
- Configuration system
- Error handling
- Module imports
- Directory structure
- Core functionality

## 📊 Output Files

### OAuth JSON Files
Generated files are saved in `output/json_files/` with format:
```
{email}_{timestamp}_oauth_client.json
```

### Reports
Processing reports are saved in `output/reports/` containing:
- Success/failure statistics
- Error details
- Processing timestamps
- File locations

### Logs
Application logs are saved in `output/logs/` with:
- Detailed operation logs
- Error traces
- Performance metrics

## 🛡️ Security Features

- **Credential Protection**: Passwords are not logged or stored
- **Secure Downloads**: Files are verified and organized safely
- **Anti-Detection**: Advanced techniques to avoid bot detection
- **Error Isolation**: Failures don't affect other accounts in batch mode

## 🔍 Troubleshooting

### Common Issues

1. **Playwright Installation**:
   ```bash
   playwright install --force chromium
   ```

2. **Permission Errors**:
   - Run as administrator on Windows
   - Check antivirus software settings

3. **Google Account Issues**:
   - Ensure 2FA is disabled or handled manually
   - Check for account security restrictions
   - Verify account credentials

4. **Network Issues**:
   - Check internet connection
   - Verify proxy settings if applicable
   - Ensure Google services are accessible

### Debug Mode

Enable debug mode by setting headless=False in settings to watch the automation process.

### Log Analysis

Check `output/logs/` for detailed error information:
- `gmail_oauth.log`: Main application log
- `error_report_*.json`: Detailed error reports

## 🔄 Migration from Selenium

This Playwright version offers several improvements over the original Selenium implementation:

- **Performance**: 2-3x faster execution
- **Reliability**: Better handling of dynamic content
- **Stealth**: Advanced anti-detection capabilities
- **Error Handling**: Comprehensive retry mechanisms
- **Monitoring**: Real-time progress tracking
- **Reporting**: Detailed success/failure analytics

## 📈 Performance Tips

1. **Batch Processing**:
   - Use concurrent_limit=2-3 for optimal performance
   - Monitor system resources during large batches

2. **Network Optimization**:
   - Stable internet connection recommended
   - Consider VPN if experiencing regional restrictions

3. **System Resources**:
   - Minimum 4GB RAM recommended
   - SSD storage for better I/O performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is for educational and automation purposes. Please ensure compliance with Google's Terms of Service and applicable laws.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review log files in `output/logs/`
3. Run the test suite: `python test_implementation.py`
4. Create an issue with detailed error information

## 🔮 Future Enhancements

- [ ] Support for additional OAuth providers
- [ ] Web-based dashboard interface
- [ ] Docker containerization
- [ ] Cloud deployment options
- [ ] Advanced scheduling features
- [ ] Integration with CI/CD pipelines

---

**Note**: This tool automates Google Cloud Console interactions. Please ensure you have appropriate permissions and comply with Google's Terms of Service.
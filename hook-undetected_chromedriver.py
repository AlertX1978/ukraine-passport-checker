"""
PyInstaller hook for undetected_chromedriver
"""
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('undetected_chromedriver')

# Additional hidden imports for undetected_chromedriver
hiddenimports += [
    'undetected_chromedriver.v2',
    'undetected_chromedriver.patcher',
    'undetected_chromedriver.options',
    'undetected_chromedriver.webelement',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.desired_capabilities',
]

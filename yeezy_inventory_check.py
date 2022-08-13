from bs4 import BeautifulSoup
import requests
import json
import smtplib
from email.message import Message
import argparse
import sys
from configparser import ConfigParser
import os

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
}


shoes = {}


def get_productIds():
    """
    Get the product Ids from Adidas website
    """
    pass


def get_list_of_available_yeezys():
    """
    Get a list of available Yeezys from Adidas website
    """
    url = "https://www.adidas.com/us/yeezy"

    yeezy_data = None
    while yeezy_data == None:
        try:

            html_data = requests.get(url, headers=headers)
            soup = BeautifulSoup(html_data.text, "html.parser")
            yeezy_data = json.loads(
                "".join(soup.find("script").strings).split("=", 1)[1]
            )
        except Exception as e:
            print(e)

    if "productIds" in yeezy_data:
        for productId in yeezy_data["productIds"]:
            html_data = requests.get(
                f"https://www.adidas.com/api/products/{productId}/availability",
                headers=headers,
            )
            print(yeezy_data["productData"][productId]["localized"]["productName"])
            print(
                f"Color: {yeezy_data['productData'][productId]['localized']['color']}"
            )
            print(
                f"Release date: {yeezy_data['productData'][productId]['localized']['comingSoonFromDate']}"
            )
            print(
                f"Stop date: {yeezy_data['productData'][productId]['localized']['onlineToDate']}"
            )
            print(
                f"Price: {yeezy_data['productData'][productId]['localized']['priceFormatted']}"
            )
            print(html_data.json())
            print(html_data.url)
            print("\n")


class LogFile:
    def __init__(self, filename):
        try:
            self.out_file = open(filename, "w")
        except:
            self.out_file = open("logfile.log", "w")
        self.old_stdout = sys.stdout
        sys.stdout = self

    def write(self, text):
        self.old_stdout.write(text)
        self.out_file.write(text)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout


def email_logfile(filename, email=None, password=None, recipient=None):
    if email and password and recipient:
        pass
    else:
        config = ConfigParser()
        config.read(os.path.expanduser("~/email_config/.config"))
        try:
            email = config.get("MAIL_CONFIG", "SENDER_EMAIL")
            password = config.get("MAIL_CONFIG", "SENDER_PASSWD")
            recipient = config.get("MAIL_CONFIG", "RECIPIENT_EMAIL")
        except:
            print(
                "Unable to email log file because email authentication is not properly setup."
            )
            return None
    try:
        with open(filename, "rb") as f:
            logs = f.read()
    except:
        with open("logfile.log", "rb") as f:
            logs = f.read()

    message = Message()
    message.set_payload(logs)
    subject = "Daily Yeezy Availability Listing"
    try:
        session = smtplib.SMTP("smtp.gmail.com", 587)
        session.ehlo()
        session.starttls()
        session.ehlo()
        session.login(email, password)
        data = f"Subject: {subject} \n {message}"
        session.sendmail(email, recipient, data)
        session.quit()
    except Exception as e:
        print(e)


def main():
    parser = argparse.ArgumentParser(
        description="Automate Yeezy Sneaker Availability Check"
    )
    parser.add_argument(
        "-e",
        "--email",
        nargs=1,
        action="store",
        dest="email",
        default=None,
        help="username for smtp",
    )
    parser.add_argument(
        "-p",
        "--password",
        nargs=1,
        action="store",
        dest="password",
        default=None,
        help="password for smtp",
    )
    parser.add_argument(
        "-r",
        "--recipient",
        nargs=1,
        action="store",
        dest="recipient",
        default=None,
        help="recipient for the email log",
    )
    args = parser.parse_args()
    logfilepath = "logfile.log"

    with LogFile(None):
        get_list_of_available_yeezys()

    if (
        type(args.email) == list
        and type(args.password) == list
        and type(args.recipient) == list
    ):
        email_logfile(logfilepath, args.email[0], args.password[0], args.recipient[0])
    else:
        email_logfile(logfilepath)


if __name__ == "__main__":
    main()

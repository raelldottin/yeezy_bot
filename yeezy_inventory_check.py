from bs4 import BeautifulSoup
import requests
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse
import sys
from configparser import ConfigParser
import os

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
}


shoes = {}


def get(url):
    """
    Perfoms HTTP GET request
    """
    data = requests.get(url, headers=headers)
    try:
        data.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if data.status_code == 404:
            pass
        else:
            print(e)
    except requests.exceptions.RequestException as e:
        print(e)

    return data


def get_yeezy_sizes(url):
    shoe_sizes = []
    data = get(url)
    if data.status_code == 404:
        print("No sizes are available.<br>")
        return False
    data = data.json()
    if data["availability_status"] == "PREVIEW":
        print("Only available on the Confirm App.<br>")
        return False

    for size_data in data["variation_list"]:
        if size_data["availability_status"] == "IN_STOCK":
            shoe_sizes.append(size_data["size"])

    if len(shoe_sizes) < 1:
        print("No sizes are available.<br>")
        return False
    else:
        print(f"Available Sizes: {', '.join(shoe_sizes)}.<br>")
        return True


def get_list_of_available_yeezys():
    """
    Get a list of available Yeezys from Adidas website
    """
    url = "https://www.adidas.com/us/yeezy"

    yeezy_data = None
    while yeezy_data == None:
        try:

            html_data = get(url)
            soup = BeautifulSoup(html_data.text, "html.parser")
            yeezy_data = json.loads(
                "".join(soup.find("script").strings).split("=", 1)[1]
            )
        except Exception as e:
            pass

    if "productIds" in yeezy_data:
        for productId in yeezy_data["productIds"]:
            print("<p>")
            print(
                f"<h2>{yeezy_data['productData'][productId]['localized']['productName']}</h2>"
            )
            print(
                f"Color: {yeezy_data['productData'][productId]['localized']['color']}<br>"
            )
            print(
                f"Release Date: {yeezy_data['productData'][productId]['localized']['releaseDate']}<br>"
            )
            print(
                f"Stop Date: {yeezy_data['productData'][productId]['localized']['onlineToDate']}<br>"
            )
            print(
                f"Price: {yeezy_data['productData'][productId]['localized']['priceFormatted']}<br>"
            )
            get_yeezy_sizes(
                f"https://www.adidas.com/api/products/{productId}/availability"
            )
            for image in yeezy_data["productData"][productId]["shared"]["imageUrls"]:
                print(f"<img src='{image}'>")
                print("<br>")
            print("</p>")


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
        with open(filename, "r") as f:
            logs = f.read()
    except:
        with open("logfile.log", "r") as f:
            logs = f.read()

    message = MIMEMultipart()
    message["From"] = email
    message["To"] = recipient
    message["Subject"] = "Daily Yeezy Availability Listing"
    message.attach(MIMEText(logs, "html"))
    message = message.as_string()
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email, password)
        server.sendmail(email, recipient, message)


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
        print("<html>")
        print("<body>")
        get_list_of_available_yeezys()
        print("</body>")
        print("</html>")

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

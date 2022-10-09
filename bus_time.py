import argparse
from bs4 import BeautifulSoup
import requests
import time
import os
from datetime import datetime

from art import text2art
from colorama import Fore, Back
from colorama import init as colorama_init


colorama_init(autoreset=True)


TFL_URL = "https://tfl.gov.uk/"
BUS_LINE_STOPS_URL = "https://tfl.gov.uk/bus/route/{bus_number}/?direction={in_or_out}"


def fetch_page(url):
    """ Fetch a page given the url """

    try:
        resp = requests.get(url)
        if not resp.ok:
            print(f"Failed getting page: {url} resp: {resp}")
            return None
        return resp.content
    except Exception as e:
        print(
            f"Failed getting page: {url} ex: {e}"
        )

    return None


def find_link_for_bus_stop(bus_route_page, bus_stop_name):
    """ Given the page for the bus route, find the link for the input bus stop """
    soup = BeautifulSoup(bus_route_page, "html.parser")

    destination = None
    bus_stop_link = None
    h1s = soup.select("h1")
    for h1 in h1s:
        text = h1.text
        if text.startswith("Towards"):
            destination = text.replace("Towards ", "")

    links = soup.select("a.stop-link")
    for link in links:
        link_text = link.text
        if bus_stop_name.lower() in link_text.lower():
            bus_stop_link = link.get('href')
            break

    return bus_stop_link, destination


def find_arrival_times(bus_stop_page):
    """ Given a bus stop page for one bus route, extract the bus arrival times"""
    soup = BeautifulSoup(bus_stop_page, "html.parser")
    arrival_items = soup.select("li.live-board-feed-item")
    times = []
    for item in arrival_items:
        eta = item.select_one("span.live-board-eta")
        if eta:
            times.append(eta.text)

    return times


def get_arrival_times(args):
    bus_route_url = BUS_LINE_STOPS_URL.format(bus_number=args.bus_number, in_or_out=args.inbound_or_outbound)
    bus_route_page = fetch_page(bus_route_url)
    bus_stop_relative_url, destination = find_link_for_bus_stop(bus_route_page, args.bus_stop_name)

    if not bus_stop_relative_url:
        print(f"Could not get bus_stop_link for {args}")
        return

    bus_stop_url = f"{TFL_URL}{bus_stop_relative_url}"
    bus_stop_page = fetch_page(bus_stop_url)
    arrival_times = find_arrival_times(bus_stop_page)
    return arrival_times, destination


def main(args):

    ordinal_numbers = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th']
    while True:
        os.system('clear')
        arrival_times, destination = get_arrival_times(args)
        time_now = datetime.now().strftime("%c")
        print(f"Bus {args.bus_number} to {destination} at stop '{args.bus_stop_name.title()}'")
        for index, arrival_time in enumerate(arrival_times):
            if not arrival_time:
                continue
            if args.big_text:
                arrival_time = arrival_time.replace("mins", "m")
                left_margin = " " * 10
                arrival_time = f"{arrival_time:>10}{left_margin}"  # align left and use space-padding
                big_arrival_time = text2art(arrival_time, font='Big')
                print(Fore.GREEN + Back.BLACK + big_arrival_time)
            else:
                print(f"{ordinal_numbers[index]}                              {arrival_time}")

        print(f"{time_now}")
        time.sleep(30)


if __name__ == "__main__":

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='London bus times')
    parser.add_argument('--bus-number', type=str,
                        help='The number identifying the bus')
    parser.add_argument('--bus-stop-name', type=str,
                        help='The name of the stop (e.g. "St Pauls")')
    parser.add_argument('--inbound-or-outbound', type=str, default='inbound',
                        help='The direction of the bus route: inbound or outbound')
    parser.add_argument('--big-text', type=bool, default=False, nargs='?',
                        help='Show the bus times in big text (for small screens)')

    args = parser.parse_args()

    main(args)

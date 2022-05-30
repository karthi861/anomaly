from bs4 import BeautifulSoup


def compare():
    with open('detection/secure.xml', 'r') as f:
        data = f.read()
        Bs_data = BeautifulSoup(data, "xml")
        value = Bs_data.findChild = 'POST'
        return value


def compose():
    with open('detection/secure.xml', 'r') as f:
        data = f.read()
        Bs_data = BeautifulSoup(data, "xml")
        value = Bs_data.findChild = 'GET'
        return value

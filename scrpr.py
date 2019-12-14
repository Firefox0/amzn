import grequests
from bs4 import BeautifulSoup
import json
import secrets
import os 

# restructure 

random = secrets.SystemRandom()

def get_user_input():
    product_formatted = None
    price_range = None 
    pages_amount = None

    user_input_raw = input("Optional Args:\n" +
                            f"{' ':15}--p X-Y (Price Range: $X-$Y, default: None)\n" +
                            f"{' ':15}--s X (Checks X pages for sales, default: 12)\n" +
                            "Example:\n" +
                            f"{' ':9}Razer Mechanical Keyboard --s 20 --p 50-100\n" +
                            f"{' ':9}(Looks for keyboard deals by checking 20 pages and considering the price range of $50-$100)\n" +
                            "Input: ")

    if "--" in user_input_raw:
        split = user_input_raw.split("--")
        product_formatted = split[0].strip()
        if " " in product_formatted:
            product_formatted.replace(" ", "+")

        for e in split[1:]:
            arg = e[:2]
            if arg == "p ":
                price_range = e[2:]
                price_range = tuple(map(float, price_range.split("-")))
            elif arg == "s ":
                pages_amount = e[2:] 

        if pages_amount:
            pages_amount = int(pages_amount)
    
    else:
        product_formatted = user_input_raw

    return product_formatted, price_range, pages_amount
    

def amazon_links(product_formatted, pages_amount=12):
    if not pages_amount:
         pages_amount = 12 

    urls = []
    amazon_standard = "https://www.amazon.com/s?k="
    for i in range(1, pages_amount+1):
        urls.append(f"{amazon_standard}{product_formatted}&page={i}")
    return urls

def make_requests(urls, header):
    print("\nStarting requests")
    async_requests = (grequests.get(u, headers=header) for u in urls)
    responses = grequests.map(async_requests) 
    print("Requests done\n")
    return responses

def filter_pages(responses, price_range=None):
    if price_range:
        minimum_range = price_range[0]
        maximum_range = price_range[1]

    filtered = []
    amount_sales_total = 0
    current_page_number = 1

    for response in responses:
        soup = BeautifulSoup(response.content, "html.parser")
        top_classes = soup.find_all("a", {"class": "a-size-base a-link-normal s-no-hover a-text-normal"})
        sale_classes = [c for c in top_classes if c.find("span", {"class": "a-price a-text-price"})]
        amount_sales_page = 0

        for sale_class in sale_classes: 
            href = sale_class["href"].split("/ref")[0]
            if href == "/gp/slredirect/picassoRedirect.html":
                continue
            prices = sale_class.find_all("span", {"class": "a-offscreen"})
            from_price = float(prices[1].text[1:].replace(",", ""))
            to_price = float(prices[0].text[1:].replace(",", ""))
            if price_range: 
                if not (to_price <= maximum_range and to_price >= minimum_range):
                    continue  
            filtered.append((from_price, to_price, href))
            amount_sales_page += 1

        amount_sales_total += amount_sales_page
        current_page_number += 1
        print_progress(f"Checking page: {current_page_number} -> Found {amount_sales_page} sales.")
    
    print_progress("")
    print(f"Checked {amount_sales_total} sales in total.\n")
    return filtered

def sort_list(l):
    l.sort(key=lambda x: x[0]-x[1], reverse=True)
    return l

def get_json(l):
    d = {h.split("/", 2)[1].replace("-", " "): {"from": f, "to": t, "saving": round(f-t, 2), "link": f"https://www.amazon.com{h}"} for f, t, h in l}
    return json.dumps(d, indent=4)
    
def write_json(json, name=random.randint(0, 1000001), dirname="best_deals"):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    with open(f"{dirname}\\{name}.json", "w") as f:
        f.write(json)

def print_progress(message):
    print(f"{message:50}\r", end="")

def main():
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}

    product_formatted, price_range, pages_amount = get_user_input()
    urls = amazon_links(product_formatted, pages_amount=pages_amount)
    responses = make_requests(urls, header)
    filtered_pages = filter_pages(responses, price_range=price_range)

    if filtered_pages:
        sorted_list = sort_list(filtered_pages)
        print(f"You save ${round(sorted_list[0][0]-sorted_list[0][1], 2)} with the best deal: https://www.amazon.com{sorted_list[0][2]}\n")

        json = get_json(sorted_list)

        name = product_formatted.lower()
        if price_range:
            name += f"_{price_range[0]}-{price_range[1]}"
        if pages_amount:
            name += f"_{pages_amount}"
        name = name.replace(" ", "_")
        write_json(json, name)
        print(f"A sorted and detailed list of the deals has been saved as {name}.json")
    else:
        print("No deals found. Look for another product or change price range.")
        
    if input("\nAgain? (y/n) ") == "y":
        main()

if __name__ == "__main__":
    main()

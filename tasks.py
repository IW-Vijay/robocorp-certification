from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.FileSystem import FileSystem



@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    orders = get_orders()
    page = open_robot_order_website(orders)
    receipt_to_archive = []
    for order in orders:
        close_popup(page)
        fill_the_from(page, order)
        store_receipt_as_pdf(page, order["Order number"])
        screenshot_receipt(page, order["Order number"])
        receipt = embed_screenshot_to_receipt(order["Order number"])
        receipt_to_archive.append(receipt)
        order_another_robot(page)
    archive_receipts(receipt_to_archive)




def get_orders():
    """Dwonload order file from given URL"""
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite= True)
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders


def open_robot_order_website(orders):
    """Opne website"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    page = browser.page()
    return page
    
def close_popup(page):
    """Deal with the popup"""
    page.click('//*[@id="root"]/div/div[2]/div/div/div/div/div/button[2]')


def fill_the_from(page, order):
    """Fill the form"""
    page.select_option("#head", order["Head"])
    page.click(f'//*[@id="root"]/div/div[1]/div/div[1]/form/div[2]/div/div[{order["Body"]}]/label')
    page.fill('//*[@id="root"]/div/div[1]/div/div[1]/form/div[3]/input', order["Legs"])
    page.fill("#address", order["Address"])
    while True:
        page.click("#order")
        
        if not page.locator("//div[@class='alert alert-danger']").is_visible():
            break


def screenshot_receipt(page, order_number):
    """Take screenshot of receipt"""
    page.screenshot(path=f"output/receipt_{order_number}.png")

def store_receipt_as_pdf(page, order_number):
    """Store receipt as PDF"""
    receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, f"output/receipt_{order_number}.pdf")  

def embed_screenshot_to_receipt(order_number):
    """Combine pdf and screenshot in pdf"""
    pdf = PDF()
    filesystem = FileSystem()
    pdf.add_files_to_pdf(
        files=[f"output/receipt_{order_number}.pdf",f"output/receipt_{order_number}.png"],
        target_document=f"output/receipt_{order_number}.pdf"
    )
    filesystem.remove_file(f"output/receipt_{order_number}.png")
    return f"receipt_{order_number}.pdf"


def order_another_robot(page):
    """Move to another order"""
    page.click('#order-another')
    
def archive_receipts(receipt_to_archive):
    """Create zip of all the receipt"""
    fileSystem = FileSystem()
    archive = Archive()
    fileSystem.create_directory("output/archived_receipts")
    for receipt in receipt_to_archive:
        fileSystem.move_file(f"output/{receipt}", destination=f"output/archived_receipts/{receipt}")
    
    archive.archive_folder_with_zip(f"output/archived_receipts", archive_name=f"output/archived_receipts.zip")
    fileSystem.remove_directory(f"output/archived_receipts", recursive= True)
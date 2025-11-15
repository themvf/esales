"""
Add shops to the database
Run this to populate the database with shops to track
"""

from database import Database

# List your shops here
SHOPS_TO_TRACK = [
    "YourShopName1",
    "YourShopName2",
    "YourShopName3",
    # Add more shops here
]

def main():
    db = Database()

    print("Adding shops to database...")
    for shop_name in SHOPS_TO_TRACK:
        db.add_shop(shop_name=shop_name)
        print(f"  ✅ Added: {shop_name}")

    print(f"\n✅ Total shops in database: {len(db.get_all_shops())}")
    db.close()
    print("\nNext step: Commit and push the database, then run the GitHub Action!")

if __name__ == '__main__':
    main()

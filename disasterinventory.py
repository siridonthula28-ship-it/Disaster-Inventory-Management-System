import sqlite3
def plot_inventory(conn):
    rows = conn.execute("""        SELECT resource, SUM(available), SUM(required)        FROM inventory        GROUP BY resource        ORDER BY resource    """).fetchall()

    if not rows:
        print("No inventory data available.")
        return

    print("\nAVAILABLE VS REQUIRED RESOURCES")
    print("-" * 45)

    for resource, available, required in rows:
        print(f"\nResource: {resource}")
        print(f"Available: {available}")
        print(f"Required: {required}")

        if available < required:
            print(f"Shortage: {required - available}")
        else:
            print("Status: Sufficient")

    print("\nInventory comparison completed.")
    print("Install matplotlib to generate a graphical chart.")

DB_NAME = ":memory:"CRITICAL_LIMIT = 0.25
COLUMNS = "resource, location, available, required"
SAMPLE_DATA = [
    ("Drinking Water", "Water", "Relief Camp A", 500, 800),
    ("Drinking Water", "Water", "Relief Camp B", 900, 850),
    ("Drinking Water", "Water", "Relief Camp C", 300, 600),
    ("Food Packets", "Food", "Relief Camp A", 1200, 1500),
    ("Food Packets", "Food", "Relief Camp B", 2000, 1800),
    ("Food Packets", "Food", "Relief Camp C", 450, 900),
    ("Medicine Kits", "Medicine", "Relief Camp A", 90, 150),
    ("Medicine Kits", "Medicine", "Relief Camp B", 160, 150),
    ("Medicine Kits", "Medicine", "Relief Camp C", 40, 120),
    ("Blankets", "Shelter", "Relief Camp A", 350, 400),
    ("Blankets", "Shelter", "Relief Camp B", 120, 300),
    ("Blankets", "Shelter", "Relief Camp C", 500, 450),]

def connect():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""        CREATE TABLE IF NOT EXISTS inventory (            id INTEGER PRIMARY KEY AUTOINCREMENT,            resource TEXT NOT NULL,            category TEXT NOT NULL,            location TEXT NOT NULL,            available INTEGER NOT NULL CHECK (available >= 0),            required INTEGER NOT NULL CHECK (required > 0),            UNIQUE (resource, location)        )    """)

    conn.commit()
    return conn

def insert_sample_data(conn):
    conn.executemany("""        INSERT OR IGNORE INTO inventory        (resource, category, location, available, required)        VALUES (?, ?, ?, ?, ?)    """, SAMPLE_DATA)

    conn.commit()

def get_status(available, required):
    shortage = max(required - available, 0)

    if shortage == 0:
        return shortage, "Sufficient"

    if shortage / required >= CRITICAL_LIMIT:
        return shortage, "Critical Shortage"

    return shortage, "Minor Shortage"

def add_resource(conn, resource, category, location,
                 available, required):
    try:
        conn.execute("""            INSERT INTO inventory            (resource, category, location, available, required)            VALUES (?, ?, ?, ?, ?)        """, (resource, category, location, available, required))

        conn.commit()
        print("Resource added successfully.")

    except sqlite3.IntegrityError:
        print("Error: Duplicate record or invalid values.")

def update_resource(conn, resource, location,
                    available, required):
    try:
        cur = conn.execute("""            UPDATE inventory            SET available = ?, required = ?            WHERE resource = ? AND location = ?        """, (available, required, resource, location))

        conn.commit()

        if cur.rowcount:
            print("Record updated successfully.")
        else:
            print("Record not found.")

    except sqlite3.IntegrityError:
        print("Error: Available must be >= 0 and required must be > 0.")

def remove_resource(conn, resource, location):
    cur = conn.execute("""        DELETE FROM inventory        WHERE resource = ? AND location = ?    """, (resource, location))

    conn.commit()

    if cur.rowcount:
        print("Record removed successfully.")
    else:
        print("Record not found.")

def print_table(rows):
    print(
        f"{'Resource':<20}{'Location':<20}"
        f"{'Available':>10}{'Required':>10}"
        f"{'Shortage':>10} Status"
    )

    print("-" * 90)

    for resource, location, available, required in rows:
        shortage, status = get_status(available, required)

        print(
            f"{resource:<20}{location:<20}"
            f"{available:>10}{required:>10}"
            f"{shortage:>10} {status}"
        )

def show_inventory(conn):
    rows = conn.execute(
        f"SELECT {COLUMNS} FROM inventory "
        "ORDER BY resource, location"
    ).fetchall()

    if rows:
        print_table(rows)
    else:
        print("Inventory is empty.")

def search_resource(conn, keyword):
    pattern = f"%{keyword}%"

    rows = conn.execute("""        SELECT resource, location, available, required        FROM inventory        WHERE resource LIKE ?           OR location LIKE ?           OR category LIKE ?        ORDER BY resource, location    """, (pattern, pattern, pattern)).fetchall()

    if rows:
        print_table(rows)
    else:
        print("No matching resources found.")

def identify_shortages(conn):
    rows = conn.execute(
        f"SELECT {COLUMNS} FROM inventory"
    ).fetchall()

    critical = [
        row for row in rows
        if get_status(row[2], row[3])[1] == "Critical Shortage"
    ]

    critical.sort(
        key=lambda row: max(row[3] - row[2], 0),
        reverse=True
    )

    print("Critical shortages found:", len(critical))

    if critical:
        print_table(critical)
    else:
        print("No critical shortages found.")

def compare_availability(conn):
    rows = conn.execute("""        SELECT resource, SUM(available), SUM(required)        FROM inventory        GROUP BY resource        ORDER BY resource    """).fetchall()

    print(
        f"{'Resource':<20}{'Available':>12}"
        f"{'Required':>12}{'Coverage':>12}"
    )

    print("-" * 56)

    for resource, available, required in rows:
        coverage = available / required * 100

        print(
            f"{resource:<20}{available:>12}"
            f"{required:>12}{coverage:>11.1f}%"
        )

def locations_needing_supplies(conn):
    rows = conn.execute("""        SELECT location, resource, available, required        FROM inventory    """).fetchall()

    summary = {}

    for location, resource, available, required in rows:
        shortage, status = get_status(available, required)

        entry = summary.setdefault(location, [0, 0])
        entry[0] += shortage

        if status == "Critical Shortage":
            entry[1] += 1

    print(
        f"{'Location':<22}{'Units Short':>14}"
        f"{'Critical Items':>17}"
    )

    print("-" * 53)

    ranked = sorted(
        summary.items(),
        key=lambda item: item[1][0],
        reverse=True
    )

    for location, (units, critical) in ranked:
        print(f"{location:<22}{units:>14}{critical:>17}")

def generate_report(conn, filename="emergency_report.txt"):
    rows = conn.execute(
        f"SELECT {COLUMNS} FROM inventory"
    ).fetchall()

    counts = {
        "Sufficient": 0,
        "Minor Shortage": 0,
        "Critical Shortage": 0
    }

    for _, _, available, required in rows:
        status = get_status(available, required)[1]
        counts[status] += 1

    with open(filename, "w", encoding="utf-8") as file:
        file.write("EMERGENCY INVENTORY REPORT\n")
        file.write("=" * 35 + "\n")
        file.write(f"Total records: {len(rows)}\n")

        for status, count in counts.items():
            file.write(f"{status:<20}: {count}\n")

    with open(filename, "r", encoding="utf-8") as file:
        print(file.read())

    print("Report saved as", filename)

def plot_inventory(conn):
    rows = conn.execute("""        SELECT resource, SUM(available), SUM(required)        FROM inventory        GROUP BY resource        ORDER BY resource    """).fetchall()

    if not rows:
        print("No inventory data available to plot.")
        return

    names = [row[0] for row in rows]
    available = [row[1] for row in rows]
    required = [row[2] for row in rows]

    x = list(range(len(names)))
    width = 0.4

    plt.figure(figsize=(9, 5))

    plt.bar(
        [i - width / 2 for i in x],
        available,
        width,
        label="Available"
    )

    plt.bar(
        [i + width / 2 for i in x],
        required,
        width,
        label="Required"
    )

    plt.xticks(x, names, rotation=20, ha="right")
    plt.ylabel("Units")
    plt.title("Available vs Required Resources")
    plt.legend()
    plt.tight_layout()

    plt.savefig("inventory_chart.png")
    plt.show()
    plt.close()

    print("Chart saved as inventory_chart.png")

def read_integer(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid whole number.")

def main():
    conn = connect()

    try:
        insert_sample_data(conn)

        menu = """========== DISASTER INVENTORY MANAGEMENT SYSTEM ==========
1. Add Resource2. Update Resource3. Remove Resource4. Show Inventory5. Search Resource6. Identify Critical Shortages7. Compare Availability8. Locations Needing Supplies9. Generate Emergency Report10. Plot Inventory Chart0. Exit
=========================================================="""

        while True:
            print(menu)
            choice = input("Enter your choice: ").strip()

            try:
                if choice == "1":
                    resource = input("Resource name: ").strip()
                    category = input("Category: ").strip()
                    location = input("Location: ").strip()
                    available = read_integer("Available quantity: ")
                    required = read_integer("Required quantity: ")

                    add_resource(
                        conn, resource, category, location,
                        available, required
                    )

                elif choice == "2":
                    resource = input("Resource name: ").strip()
                    location = input("Location: ").strip()
                    available = read_integer("New available quantity: ")
                    required = read_integer("New required quantity: ")

                    update_resource(
                        conn, resource, location,
                        available, required
                    )

                elif choice == "3":
                    resource = input("Resource name: ").strip()
                    location = input("Location: ").strip()

                    remove_resource(conn, resource, location)

                elif choice == "4":
                    show_inventory(conn)

                elif choice == "5":
                    keyword = input("Enter search keyword: ").strip()
                    search_resource(conn, keyword)

                elif choice == "6":
                    identify_shortages(conn)

                elif choice == "7":
                    compare_availability(conn)

                elif choice == "8":
                    locations_needing_supplies(conn)

                elif choice == "9":
                    generate_report(conn)

                elif choice == "10":
                    plot_inventory(conn)

                elif choice == "0":
                    print("Exiting the system. Goodbye!")
                    break

                else:
                    print("Invalid choice. Please try again.")

            except sqlite3.Error as error:
                print("Database error:", error)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
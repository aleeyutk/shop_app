import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
from app.models import Base, Category, Product

logger = logging.getLogger("shop.database")
settings = get_settings()

# Engine creation based on database dialect
if settings.is_postgres:
    engine = create_engine(
        settings.normalized_database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
else:
    engine = create_engine(
        settings.normalized_database_url,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data(db: Session):
    """Seed initial categories and products if database is fresh."""
    if db.query(Category).first() is not None:
        return

    logger.info("Seeding initial shop categories and products...")

    electronics = Category(
        name="Electronics",
        slug="electronics",
        description="Cutting-edge tech, personal audio, and everyday gadgets.",
        icon="laptop",
    )
    apparel = Category(
        name="Apparel & Footwear",
        slug="apparel",
        description="Premium everyday essentials crafted for comfort and style.",
        icon="shirt",
    )
    home = Category(
        name="Home & Living",
        slug="home-living",
        description="Thoughtfully designed pieces to elevate your workspace and home.",
        icon="home",
    )
    accessories = Category(
        name="Accessories",
        slug="accessories",
        description="Everyday carry, travel gear, and sleek essentials.",
        icon="watch",
    )

    db.add_all([electronics, apparel, home, accessories])
    db.flush()

    products = [
        # Electronics
        Product(
            name="Aura Pro Wireless ANC Headphones",
            slug="aura-pro-wireless-anc-headphones",
            description="High-fidelity audio with active hybrid noise cancellation, 40-hour battery life, ultra-soft memory foam earcups, and multipoint Bluetooth 5.3 connection.",
            price=249.99,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
            category_id=electronics.id,
            stock=45,
            is_featured=True,
            rating=4.9,
            reviews_count=128,
        ),
        Product(
            name="Pulse Horizon Smart Fitness Watch",
            slug="pulse-horizon-smart-fitness-watch",
            description="Ultra-vivid AMOLED display, continuous heart-rate & SpO2 monitoring, GPS tracking, 7-day battery life, and 50m water resistance.",
            price=179.50,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
            category_id=electronics.id,
            stock=30,
            is_featured=True,
            rating=4.7,
            reviews_count=84,
        ),
        Product(
            name="KeyFlow Custom Wireless Mechanical Keyboard",
            slug="keyflow-wireless-mechanical-keyboard",
            description="Hot-swappable tactile switches, CNC aluminum chassis, RGB backlighting, low-latency 2.4GHz wireless and Bluetooth.",
            price=139.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80",
            category_id=electronics.id,
            stock=22,
            is_featured=False,
            rating=4.8,
            reviews_count=67,
        ),
        Product(
            name="ViewSonic Clarity 4K Ultra-Wide Monitor",
            slug="viewsonic-clarity-4k-ultrawide-monitor",
            description="34-inch curved IPS display with 99% sRGB color gamut, USB-C 90W power delivery, 144Hz refresh rate, and anti-glare coating.",
            price=499.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80",
            category_id=electronics.id,
            stock=15,
            is_featured=False,
            rating=4.9,
            reviews_count=42,
        ),

        # Apparel
        Product(
            name="Heavyweight French Terry Cotton Hoodie",
            slug="heavyweight-french-terry-cotton-hoodie",
            description="Crafted from 480 GSM organic cotton with custom drop shoulders, double-layered hood, and durable ribbed cuffs.",
            price=89.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=800&q=80",
            category_id=apparel.id,
            stock=60,
            is_featured=True,
            rating=4.8,
            reviews_count=96,
        ),
        Product(
            name="Vanguard Minimalist Leather Low-Tops",
            slug="vanguard-minimalist-leather-low-tops",
            description="Handcrafted Italian nappa leather sneakers with cushioned orthotic insole, margom rubber outsole, and waxed cotton laces.",
            price=145.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=80",
            category_id=apparel.id,
            stock=35,
            is_featured=True,
            rating=4.9,
            reviews_count=110,
        ),
        Product(
            name="All-Weather Modular Commuter Jacket",
            slug="all-weather-modular-commuter-jacket",
            description="Windproof, breathable, 3-layer waterproof shell with taped seams, magnetic storm flap, and hidden device pockets.",
            price=195.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1544441893-675973e31985?auto=format&fit=crop&w=800&q=80",
            category_id=apparel.id,
            stock=25,
            is_featured=False,
            rating=4.6,
            reviews_count=39,
        ),
        Product(
            name="Aerolite Everyday Tech Backpack 24L",
            slug="aerolite-everyday-tech-backpack-24l",
            description="Water-resistant ballistic nylon with dedicated 16-inch padded laptop sleeve, quick-access passport pocket, and luggage pass-through.",
            price=119.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80",
            category_id=apparel.id,
            stock=40,
            is_featured=False,
            rating=4.8,
            reviews_count=73,
        ),

        # Home & Living
        Product(
            name="Lumina Smart Ambient Desk Lamp",
            slug="lumina-smart-ambient-desk-lamp",
            description="Circadian rhythm lighting with tunable white color temperature (2700K-6500K), built-in 15W Qi wireless charging pad, and smooth touch dimmer.",
            price=78.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=80",
            category_id=home.id,
            stock=50,
            is_featured=True,
            rating=4.7,
            reviews_count=52,
        ),
        Product(
            name="Artisan Ceramic Pour-Over Coffee Dripper Set",
            slug="artisan-ceramic-pour-over-coffee-set",
            description="Handmade stoneware dripper with heat-resistant borosilicate glass carafe, walnut base, and precision stainless steel reusable filter.",
            price=64.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80",
            category_id=home.id,
            stock=38,
            is_featured=False,
            rating=4.9,
            reviews_count=64,
        ),
        Product(
            name="Aromatherapy Hand-Poured Soy Candle Trio",
            slug="aromatherapy-hand-poured-soy-candle-trio",
            description="Three 8oz amber glass candles with crackling wood wicks: Sandalwood & Amber, White Tea & Thyme, and Bergamot & Cedar.",
            price=42.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=800&q=80",
            category_id=home.id,
            stock=65,
            is_featured=False,
            rating=4.8,
            reviews_count=41,
        ),

        # Accessories
        Product(
            name="MagLock Titanium RFID Minimalist Wallet",
            slug="maglock-titanium-rfid-minimalist-wallet",
            description="Aerospace-grade grade-5 titanium plates with RFID blocking, expandable silicone band holding up to 12 cards, and integrated cash strap.",
            price=58.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=800&q=80",
            category_id=accessories.id,
            stock=70,
            is_featured=True,
            rating=4.9,
            reviews_count=145,
        ),
        Product(
            name="VoltStream MagSafe 10,000mAh Power Bank",
            slug="voltstream-magsafe-10000mah-power-bank",
            description="Snap-on wireless charging with 20W USB-C bi-directional PD fast charging, digital percentage display, and fold-out kickstand.",
            price=49.99,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1609592426867-270830425c34?auto=format&fit=crop&w=800&q=80",
            category_id=accessories.id,
            stock=55,
            is_featured=False,
            rating=4.7,
            reviews_count=89,
        ),
        Product(
            name="HydroPeak Vacuum Insulated 32oz Tumbler",
            slug="hydropeak-vacuum-insulated-32oz-tumbler",
            description="Double-wall 18/8 food-grade stainless steel keeping drinks ice cold for 24 hours or piping hot for 12 hours. Leak-proof straw lid included.",
            price=34.00,
            currency="USD",
            image_url="https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=800&q=80",
            category_id=accessories.id,
            stock=80,
            is_featured=False,
            rating=4.9,
            reviews_count=160,
        ),
    ]

    db.add_all(products)
    db.commit()
    logger.info("Successfully seeded %d categories and %d products.", 4, len(products))


def init_db():
    """Create all database tables and seed sample products."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)

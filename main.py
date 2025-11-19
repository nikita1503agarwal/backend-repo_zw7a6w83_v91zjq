import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem, CustomerInfo

app = FastAPI(title="iPhone Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductResponse(Product):
    id: str

class OrderResponse(Order):
    id: str


@app.get("/")
def read_root():
    return {"message": "iPhone Store Backend is running"}


@app.get("/api/products", response_model=List[ProductResponse])
def list_products():
    try:
        docs = get_documents("product")
        results = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            results.append(ProductResponse(**d))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products", response_model=str)
def add_product(product: Product):
    try:
        new_id = create_document("product", product)
        return new_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class CreateOrderRequest(BaseModel):
    items: List[CartItem]
    customer: CustomerInfo


@app.post("/api/orders", response_model=str)
def create_order(payload: CreateOrderRequest):
    # Build order items from product snapshots
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")

    items: List[OrderItem] = []
    total = 0.0

    for ci in payload.items:
        try:
            obj_id = ObjectId(ci.product_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid product id: {ci.product_id}")

        prod = db["product"].find_one({"_id": obj_id})
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product not found: {ci.product_id}")

        price = float(prod.get("price", 0))
        qty = max(1, int(ci.quantity))
        total += price * qty
        items.append(
            OrderItem(
                product_id=str(prod["_id"]),
                title=prod.get("title", "Product"),
                price=price,
                quantity=qty,
            )
        )

    order = Order(items=items, total=round(total, 2), customer=payload.customer)

    try:
        order_id = create_document("order", order)
        return order_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

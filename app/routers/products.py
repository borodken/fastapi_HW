from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from typing import Annotated

from app.models import *
from sqlalchemy import insert, select, update
from app.schemas import CreateProduct

from slugify import slugify

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/")
async def get_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where((Product.is_active) & (Product.stock > 0)))

    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No products found"
        )

    return products.all()


@router.get("/{category_slug}")
async def get_products_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No product found"
        )

    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id))

    category_and_subcategories = [category.id] + [cat.id for cat in subcategories.all()]

    products =  await db.scalars(select(Product).where(Product.is_active
                                                       & (Product.stock > 0)
                                                       & Product.category_id.in_(category_and_subcategories)))

    return products.all()


@router.get("/detail/{product_slug}")
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug
                                                    & Product.is_active == True
                                                    & Product.stock > 0))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No product found"
        )

    return product


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], create_product: CreateProduct):
    await db.execute(insert(Product).values(name=create_product.name,
                                            description=create_product.description,
                                            price=create_product.price,
                                            image_url=create_product.image_url,
                                            stock=create_product.stock,
                                            category_id=create_product.category,
                                            rating=0.0,
                                            slug=slugify(create_product.name)
                                            ))

    await db.commit()

    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful"
    }


@router.put("/detail/{product_slug}")
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str, update_product: CreateProduct):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await db.execute(update(Product).where(Product.slug == product_slug).values(name=update_product.name,
                                                                                description=update_product.description,
                                                                                price=update_product.price,
                                                                                image_url=update_product.image_url,
                                                                                stock=update_product.stock,
                                                                                product_id=update_product.product_id
                                                                                ))

    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Product update is successful"
    }


@router.delete("/delete")
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_id: int):
    product = await db.scalar(select(Product).where(Product.id == product_id))

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    else:
        await db.execute(update(Product).where(Product.id == product_id).values(is_active=False))

        await db.commit()

        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "product delete is successful"
        }

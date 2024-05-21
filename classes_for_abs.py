from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker



Base = declarative_base()

class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Shop(Base):
    __tablename__ = 'shops'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)

class Flower(Base):
    __tablename__ = 'flowers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    flower_count = Column(Integer)
    shop_id = Column(Integer, ForeignKey('shops.id'))
    shop = relationship('Shop')

class Bouquet(Base):
    __tablename__ = 'bouquets'
    id = Column(Integer, primary_key=True)
    flower = Column(String)
    price = Column(Float)
    shop_id = Column(Integer, ForeignKey('shops.id'))
    shop = relationship('Shop')

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    bouquet_id = Column(Integer, ForeignKey('bouquets.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    bouquet = relationship('Bouquet')
    client = relationship('Client')



class Delivery(Base):
    __tablename__ = 'deliveries'
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    shop_id = Column(Integer, ForeignKey('shops.id'))
    flower = Column(String)
    flower_count = Column(Integer)
    price = Column(Float)
    date = Column(String)
    supplier = relationship('Supplier')
    shop = relationship('Shop')

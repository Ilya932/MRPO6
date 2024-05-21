from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
from abc import ABC, abstractmethod
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import uuid4
from classes_for_abs import *
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

class AbstractRepository(ABC):

    @abstractmethod
    def add(self, entity):
        pass

    @abstractmethod
    def get(self, id, Class):
        pass

    @abstractmethod
    def list(self, Class):
        pass

    @abstractmethod
    def update(self, id, class_name, new_data):
        pass

    @abstractmethod
    def delete(self, id, class_name):
        pass

    @abstractmethod
    def delete_all_by_class(self, class_name):
        pass

    @abstractmethod
    def delete_all(self):
        pass


class JSONRepository(AbstractRepository):

    def __init__(self, file_path):
        self.file_path = file_path
        self._load()

    def _load(self):
        try:
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = []
        except json.JSONDecodeError:
            self.data = []

    def _save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def _get_next_id(self, class_name):
        class_items = [item for item in self.data if item['class'] == class_name]
        if not class_items:
            return 1
        else:
            return max(item['id'] for item in class_items) + 1



    def add(self, entity):
        class_name = entity['class']
        entity['id'] = self._get_next_id(class_name)
        self.data.append(entity)
        self._save()
        return entity


    def get(self, id, class_name):
        return next((item for item in self.data if item['id'] == id and item['class'] == class_name), None)

    def list(self, Class):
        if Class == 'all':
            return self.data
        else:
            return [item for item in self.data if item['class'] == Class]

    def update(self, id, class_name, new_data):
        for item in self.data:
            if item['id'] == id and item['class'] == class_name:
                for key, value in new_data.items():
                    item[key] = value
                self._save()
                return True
        return False

    def delete(self, id, class_name):
        for i, item in enumerate(self.data):
            if item['id'] == id and item['class'] == class_name:
                del self.data[i]
                self._save()
                return True
        return False

    def delete_all_by_class(self, class_name):
        self.data = [item for item in self.data if item['class'] != class_name]
        self._save()

    def delete_all(self):
        self.data = []
        self._save()

# Unit of Work implementation
class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory



    @contextmanager
    def __call__(self):
        session = self.session_factory()
        try:

            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()


class Business2:


    json_repo = JSONRepository('data.json')
    def delivery_flowers(self, supplier, shop, flower, flower_count, price, date):
        delivery = Delivery(
            supplier_id=supplier['id'],
            shop_id=shop['id'],
            flower=flower['name'],
            flower_count=flower_count,
            price=price,
            date=date.strftime('%Y-%m-%d')
        )
        self.json_repo.add(delivery)
        return delivery

    def create_bouquet(self, flowers, shop_id):
        price = 0

        for flower in flowers:
            flower_from_repo = self.json_repo.get(flower['id'])
            if flower_from_repo and flower_from_repo['flower_count'] >= flower['flower_count']:
                price += flower['price'] * flower['flower_count']
            else:
                return False

        bouquet = Bouquet(flower=','.join([f['name'] for f in flowers]), price=price, shop_id=shop_id)
        self.json_repo.add(bouquet)
        for flower in flowers:
            flower_from_repo = self.json_repo.get(flower['id'])
            flower_from_repo['flower_count'] -= flower['flower_count']
            self.json_repo.update(flower_from_repo)

        return bouquet

    def purchase_bouquet(self, client, bouquet):
        purchase = Purchase( bouquet_id=bouquet['id'], client_id=client['id'])
        self.json_repo.add(purchase)
        self.json_repo.delete(bouquet['id'], 'Bouquet')
        return purchase


json_repo = JSONRepository('data.json')

@app.route('/add', methods=['POST'])
def add_entity():
    data = request.json
    if 'class' not in data:
        return jsonify({"error": "Class name is required"}), 400
    entity_class = data['class']
    if entity_class not in ['Supplier', 'Client', 'Shop', 'Flower', 'Bouquet', 'Purchase', 'Delivery']:
        return jsonify({"error": "Invalid class name"}), 400
    result = json_repo.add(data)
    return jsonify(result), 201

# Ендпоинт для получения экземпляра по id и классу
@app.route('/get/<class_name>/<int:id>', methods=['GET'])
def get_entity(class_name, id):
    result = json_repo.get(id, class_name)
    if result:
        return jsonify(result), 200
    return jsonify({"error": "Entity not found"}), 404



@app.route('/list/<class_name>', methods=['GET'])
def list_entities(class_name):
    result = json_repo.list(class_name)
    return jsonify(result), 200

# Ендпоинт для обновления экземпляра по id и классу
@app.route('/update/<class_name>/<int:id>', methods=['PUT'])
def update_entity(class_name, id):
    new_data = request.json
    success = json_repo.update(id, class_name, new_data)
    if success:
        return jsonify({"message": "Entity updated"}), 200
    return jsonify({"error": "Entity not found"}), 404

# Ендпоинт для удаления экземпляра по id и классу
@app.route('/delete/<class_name>/<int:id>', methods=['POST'])
def delete_entity(id, class_name):
    success = json_repo.delete(id, str(class_name))
    if success:
        return jsonify({"message": "Entity deleted"}), 200
    return jsonify({"error": "Entity not found"}), 404

# Ендпоинт для удаления всех экземпляров определенного класса
@app.route('/delete_all_by_class/<class_name>', methods=['DELETE'])
def delete_all_by_class(class_name):
    json_repo.delete_all_by_class(class_name)
    return jsonify({"message": f"All entities of class {class_name} deleted"}), 200

# Ендпоинт для удаления всех экземпляров
@app.route('/delete_all', methods=['DELETE'])
def delete_all():
    json_repo.delete_all()
    return jsonify({"message": "All entities deleted"}), 200






def example_json_usage():


    json_repo = JSONRepository('data.json')

    # Adding a new supplier
    new_supplier = Client(name="Supplier1")
    added_supplier = json_repo.add(new_supplier)
    print(json_repo.list('all'))


#example_json_usage()

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request
from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required
import sqlite3
from resources.filtros import normalize_path_params, consulta_com_cidade, consulta_sem_cidade


class Hoteis(Resource):
    def get(self):
        path_params = {
            'cidade': request.args.get('cidade'),
            'estrelas_min': request.args.get('estrelas_min'),
            'estrelas_max': request.args.get('estrelas_max'),
            'diaria_min': request.args.get('diaria_min'),
            'diaria_max': request.args.get('diaria_max'),
            'limit': request.args.get('limit'),
            'offset': request.args.get('offset'),
        }

        connection = sqlite3.connect('instance/banco.db')
        cursor = connection.cursor()

        dados_validos = {chave: path_params[chave] for chave in path_params if path_params[chave] is not None}
        parametros = normalize_path_params(**dados_validos)
        tupla = tuple([parametros[chave] for chave in parametros])

        if not parametros.get('cidade'):
            resultado = cursor.execute(consulta_sem_cidade, tupla).fetchall()
        else:
            resultado = cursor.execute(consulta_com_cidade, tupla).fetchall()

        print(resultado)

        hoteis = []
        for linha in resultado:
            hoteis.add({
                'hotel_id': linha[0],
                'nome': linha[1],
                'estrelas': linha[2],
                'diaria': linha[3],
                'cidade': linha[4],
            })

        return {'hoteis': hoteis}





class Hotel(Resource):
    atributos = reqparse.RequestParser()
    atributos.add_argument('nome', type=str, required=True, help="The field 'nome' cannot be left blank")
    atributos.add_argument('estrelas', type=str)
    atributos.add_argument('diaria', type=str)
    atributos.add_argument('cidade', type=str, required=True, help="The field 'cidade' cannot be left blank")

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel not found.'}, 404

    @jwt_required()
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {'message': 'Hotel id {} already exists.'.format(hotel_id)}, 400

        dados = Hotel.atributos.parse_args()
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'An internal error ocurred trying to save hotel.'}, 500
        return hotel.json(), 201

    @jwt_required()
    def put(self, hotel_id):
        dados = Hotel.atributos.parse_args()
        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            hotel_encontrado.save_hotel()
            return hotel_encontrado.json(), 200
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'An internal error ocurred trying to save hotel.'}, 500
        return hotel.json(), 201

    @jwt_required()
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'An internal error ocurred trying to save hotel.'}, 500
            return {'message': 'Hotel deleted.'}, 200
        return {'message': 'Hotel not found.'}, 404
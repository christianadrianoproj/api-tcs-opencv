# -*- coding: utf-8 -*-
from random import randint
import numpy as np
import psycopg2
import os
import flask
from flask import (
	Flask,  
	request
)
import cv2 as cv

app = Flask(__name__)

@app.route('/')      
def get():
    try:
        return {"status": "success"}
    except (Exception, psycopg2.Error) as error :
        print ("Error", error)

@app.route('/imagens', methods=['GET', 'POST'])
def imagens():
    print(request.method);
    if request.method == 'POST':
        try:
            file_o = request.files['image_original']
            if file_o:
                fname_o = file_o.filename.split('.')[0]
                fextension_o = file_o.filename.split('.')[1]
                print("processamento da imagem - inicio")
                path = './imagem_'+ str(randint(0,9)) + str(randint(0,9))+ str(randint(0,9))+ str(randint(0,9))+ str(randint(0,9))+ '_' + fname_o + '.' + fextension_o
                path2 = './process_'+ str(randint(0,9)) + str(randint(0,9))+ str(randint(0,9))+ str(randint(0,9))+ str(randint(0,9))+ '_' + fname_o + '.' + fextension_o
                open(path, 'wb').write(file_o.read())
                imagem = cv.imread(path)
                
                print("Conversao RGB para HSV")
                hsv = cv.cvtColor(imagem, cv.COLOR_BGR2HSV)
                
                print("definir faixa de cor verde em HSV")
                green_low = np.array([20 , 100, 50] )
                green_high = np.array([75, 255, 255])
                
                print("Limita a imagem HSV para obter apenas cores verdes - cria uma mascara da folha")
                mask = cv.inRange(hsv, green_low, green_high)
                
                print("Conjunção bit a bit por elemento de duas matrizes(mascara e imagem original)")
                res = cv.bitwise_and(imagem,imagem, mask= mask)
                
                print("Conversao RGB para HSV novamente a imagem pré-processada")
                hsv2 = cv.cvtColor(res, cv.COLOR_BGR2HSV)
                
                print("definir faixa de cor da mancha em HSV")
                g_low  = np.array([0, 0, 230])
                g_high = np.array([50, 140, 255])
                
                print("Limita a imagem HSV para obter apenas cores das manchas - cria uma nova mascara das manchas")
                mask2 = cv.inRange(hsv2, g_low, g_high)

                print("Conjunção bit a bit por elemento de duas matrizes(nova mascara e imagem pré-processada)")
                res2 = cv.bitwise_and(res,res, mask= mask2)

                print("Retorna os objetos encontrados")
                cnts,hierarchy = cv.findContours(mask2, cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)

                print("Destaca/pinta esses objetos encontrados na imagem original")
                cv.drawContours(imagem, cnts, -1, (0, 0, 255), 3)

                cv.imwrite(path2, imagem)
                s1= 3
                s2 = 20
                xcnts = []
                for cnt in cnts:
                    if s1 < cv.contourArea(cnt) <s2:
                        xcnts.append(cnt)
                print("Quantidade de objetos/manchas encontradas: {}".format(len(xcnts)))
                print("Imagem processada com sucesso!")
                #print("grava as informacoes no banco")
                #connection = psycopg2.connect(user = "christian",
                #                  password = "agrom123@",
                #                  host = "54.159.152.182",
                #                  port = "5432",
                #                  database = "agrom")
                connection = psycopg2.connect(user = "ulxkjfywbyujip",
                                  password = "4b80874cca07eccd1939dc50ed42c9a91317a4014440dc31b8c61571429c9f10",
                                  host = "ec2-54-234-44-238.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "d6cc2md4sg8e4n")         
                cursor = connection.cursor()
                #print("SGBD - conectado");
                cursor.execute("INSERT INTO tb_foto (nome,contornos,manchas,image,image_proc,extensao) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
                               (fname_o, len(cnts), len(xcnts), psycopg2.Binary(open(path, 'rb').read()), psycopg2.Binary(open(path2, 'rb').read()), fextension_o))
                #print("SGBD - INSERT concluido");
                recset = cursor.fetchall()
                idimage = 0
                for rec in recset:
                    idimage = rec[0]
                connection.commit()
                return {"status": "success", "id_image":idimage}
            else:
                return {"status": "Failure", "id_image":0}
        except (Exception, psycopg2.Error) as error :
            print ("Error", error)
        finally:
            os.remove(path)
            os.remove(path2)
            if(connection):
                cursor.close()
                connection.close()
    else:
        return get()
    

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

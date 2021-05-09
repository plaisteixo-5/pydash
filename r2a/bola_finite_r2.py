# ================================================== #
# Universidade de Brasilia
# Departamento de Ciencia da Computacao
# Redes de Computadores - Turma A - 2020.2
# Alunos: Carlos Eduardo da Silva Andrade - 190025905
#         Daniel Rodrigues Cardoso        - 190064064
#         Felipe Fontenele dos Santos     - 190027622
# ================================================== #

from r2a.ir2a import IR2A
from player.parser import *
import time
import math

class BOLA_FINITE_r2(IR2A):

    def _init_(self, id):
        IR2A._init_(self, id)
        self.qi = []
        self.throughput = []
        self.time_request = 0
        self.parsed_mpd = 0
        self.vm = 0.0

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())                                 # Gera o parser
        self.qi = self.parsed_mpd.get_qi()                                             # Pega todas as qualidades que foram extraídas no parser

        self.send_up(msg)

    def handle_segment_size_request(self, msg):

        V = 0.0
        quality_index = 0
        quality = 0
        penult_throughput = 0.0
        m_lign = 0

        if msg.get_segment_id() != 1: 
            
            V = (self.whiteboard.get_max_buffer_size() - 1) / (self.vm + 5)            # Faz o cálculo da variável de utilidade do algoritimo.
            buffer_size = self.whiteboard.get_playback_buffer_size()[-1][1]            # Guarda o último valor do nível do buffer registrado.

            last_qualities = self.whiteboard.get_playback_qi()                         # Guarda o registro de qualidades.

            for i in range(len(self.qi)):                                              # Procura a maior qualidade que se encaixe nos requisitos do algoritimo.
                controller = math.log(self.qi[i]/self.qi[0])
                supposed_quality = (V * controller + V * 5 - buffer_size) / self.qi[i] 
                if quality < supposed_quality:
                    quality = supposed_quality
                    quality_index = i
            
            if last_qualities and self.qi[quality_index] > msg.get_quality_id():       # Para evitar o rebuffering por queda de bandwidth, este trecho de código
                                                                                       # serve para verificar se a qualidade escolhida foi maior que a qualidade
                                                                                       # que o último segmento foi baixado.
                
                penult_throughput = self.throughput[-1]                                
                for i in range(len(self.qi)):                                          # Loop para escolher a melhor qualidade usando o último throughput registrado
                                                                                       # como parâmetro.
                    if self.qi[i] < penult_throughput:
                        m_lign = i
                
                if self.qi[m_lign] >= self.qi[quality_index]:
                    m_lign = quality_index
                elif m_lign < last_qualities[-1][1]:
                    m_lign = last_qualities[-1][1]
                else:
                    m_lign = m_lign + 1
                
                quality_index = m_lign

        msg.add_quality_id(self.qi[quality_index])
        self.time_request = time.perf_counter()

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t1 = 0.0
        t1 = time.perf_counter() - self.time_request                                   # Guarda o tempo que foi necessário para fazer a requisição do segmento

        self.throughput = [ msg.get_bit_length() / t1 ]                                # Guarda a vazão
        self.vm = math.log(msg.get_quality_id() / self.qi[0])                          # Guarda o valor da variável de balanço

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

# coding:utf-8
import heapq  
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np
import itertools
import matplotlib.pyplot as plt
from matplotlib import rc
import matplotlib as mpl
import win32com.client
from pylab import *
from decimal import Decimal
from array import *
import numpy
import pdb
import math

class DSS():

    def __init__(self, end_modelo_DSS):

        self.end_modelo_DSS = end_modelo_DSS

        # Criar conexão entre Python e openDSS
        self.dssObj = win32com.client.Dispatch("OpenDSSEngine.DSS")

        # Iniciar o Objeto DSS
        if self.dssObj.Start(0) == False:
            print ("Problemas ao iniciar o OpenDSS")
        else:
            #Criar variáveis para as principais interfaces
            #Fazer para as outras variáveis globais 
            self.dssText = self.dssObj.Text
            self.dssCircuit = self.dssObj.ActiveCircuit
            self.dssSolution = self.dssCircuit.Solution
            self.dssCktElement = self.dssCircuit.ActiveCktElement
            self.dssBus = self.dssCircuit.ActiveBus
            self.dssLines = self.dssCircuit.Lines
            self.dssTransformers = self.dssCircuit.Transformers
            self.dssCapacitors = self.dssCircuit.Capacitors
            self.dssSwtControls = self.dssCircuit.SwtControls
            global equip_select


    def versao_DSS(self):

        return self.dssObj.Version

    def compile_DSS(self):
        #Limpar informações da ultima simulação
        self.dssObj.ClearAll()  
        self.dssText.Command = "compile " + self.end_modelo_DSS 

    def solve_DSS_snapshot(self, multiplicador_carga):

        #Configurações
        self.dssText.Command = "Set Mode = SnapShot"
        self.dssText.Command = "Set ControlMode = Static"

        #Multiplicar o valor nominal das cargas pelo valor multiplicador_carga
        self.dssSolution.LoadMult = multiplicador_carga

        #Resolver fluxo de potência
        self.dssSolution.Solve()

    def getBusHighestDeviation(self):
        vpu = self.dssCircuit.AllBusVmagPu
        buses = self.dssCircuit.AllBusNames
        deltaVi1 = [] 
        deltaVi2 = []
        dict_Vi = {} #para poder printar os desvios com clareza
        for i in range(int(len(vpu))):
            if vpu[i] >= 1: 
                delta = vpu[i] - Vmax
                dict_Vi.update({vpu[i]:delta})
                print("O desvio da barra " + str(i) + " e: " + str(delta))
            elif vpu[i] < 1:                 
                deltha = Vmin - vpu[i]
                dict_Vi.update({vpu[i]:deltha})
                print("O desvio da barra " + str(i) + " e: " + str(deltha)) 
  
        max_desvio = max(dict_Vi.values())
        list_Vi = list(dict_Vi.values())  # a posição em que o desvio máximo se encontra nessa lista corresponde à barra que apresenta o maior desvio e que precisa ser realizada o VVC
        global id_barra
        id_barra = list_Vi.index(max_desvio)
        global list_buses
        list_buses = []
        for i in range(len(self.dssCircuit.AllNodeNames)):
            list_buses.append(self.dssCircuit.AllNodeNames[i])

        for j in range(len(list_buses)):
            if id_barra == j: #se esse equip for o mais efetivo.
                print("\Barra Ativa: {}".format(objeto.ativa_barra(list_buses[j])))
                print("A barra {} , indexada como {}, foi a identificada para a realização do VVC".format(list_buses[j], id_barra))
                break
        

        return id_barra, max_desvio

    def get_AllBusVmagPu(self):

        Vi = self.dssCircuit.AllBusVmagPu

        return Vi

    def solve_Pflow(self):

        #Configurações
        self.dssText.Command = "Set Mode = SnapShot"
        self.dssText.Command = "Set ControlMode = OFF"
    
    def ativa_elemento(self, nome_elemento):

        # Ativa elemento pelo seu nome completo Tipo.Nome
        self.dssCircuit.SetActiveElement(nome_elemento)

        # Retonar o nome do elemento ativado
        return self.dssCktElement.Name
    
    def ativa_barra(self, nome_barra):

        # Ativa barra pelo seu nome
        self.dssCircuit.SetActiveBus(nome_barra)
    
        # Retornar o nome da barra ativada
        return self.dssBus.Name

    def efetividade(self):
        Vi = objeto.get_AllBusVmagPu()
        Vin = list(Vi)
        desvio_trafos = []
        desvio_cap = []
        effectiveness = []
        dict_allVoltages_trafos = {}
        VoltagesPerTrafos = []
        penalizado_real_escolhido = []
        equip_ajustar = None
        penalizado = 0
        id_barra, max_desvio = objeto.getBusHighestDeviation()

        val_tensoes = [i for i in Vin] # para não ter que criar um for para as impressões de baixo
        print("O valor máximo das tensões é {} pu".format(max(val_tensoes)))
        print("O valor mínimo das tensões é {} pu".format(min(val_tensoes)))
        desvio1 = max(val_tensoes) - Vmax
        desvio2 = Vmin - min(val_tensoes)
        print("O maior desvio encontrado é: " + str(max_desvio))
        buss1 = [i for i in Vin if i < 0.94]
        barras_violadas1 = len(buss1) # corresponde ao número de barras violadas abaixo de 0.94
        buss2 = [i for i in Vin if i > 1.05]
        barras_violadas2 = len(buss2) # corresponde ao número de barras violadas acima de 1.05
        global all_bus_wrong
        all_bus_wrong = barras_violadas1 + barras_violadas2
        print("O circuito possui {} barras violadas\n".format(all_bus_wrong))

    # Caso o elemento ativo for um banco de capacitores:
        # Seleciona o primeiro
        dict_caps = {}
        global list_caps
        list_caps = []
        self.dssCapacitors.First
        passos = self.dssCapacitors.NumSteps
        global estados
        estados = self.dssCapacitors.States
        Vi = objeto.get_AllBusVmagPu()
        Vin = list(Vi)
        id_tensao = Vin[id_barra] # id_tensao corresponde à tensão com maior desvio e a que vamos analisar no VVC

        for i in range(self.dssCapacitors.Count):
            list_caps.append(self.dssCktElement.Name)
            self.dssCapacitors.Next
        
        self.dssCapacitors.First
        for i in range(self.dssCapacitors.Count):
            print("Elemento selecionado: " + self.dssCktElement.Name)
            print("Estado atual: {}".format(estados))
            if estados == (1,):
                self.dssCapacitors.Open()
            elif estados == (0,):
                self.dssCapacitors.Close()

            self.dssText.Command = 'solve mode=snapshot'
            if max_desvio == Vmin - min(val_tensoes):
                Vi = objeto.get_AllBusVmagPu()
                Vin = list(Vi)
                tensao_iter = Vin[id_barra]
                print("Tensão atualizada: " + str(tensao_iter))
                desvio = id_tensao - tensao_iter
                desvio_cap.append(abs(desvio))
            elif max_desvio == max(val_tensoes) - Vmax:
                Vi = objeto.get_AllBusVmagPu()
                Vin = list(Vi)
                tensao_iter = Vin[id_barra]
                print("Tensão atualizada: " + str(tensao_iter))
                desvio = id_tensao - tensao_iter
                desvio_cap.append(abs(desvio))
            print(estados)
            if estados == (1,):
                self.dssCapacitors.Close()
            elif estados == (0,):
                self.dssCapacitors.Open()
            self.dssText.Command = 'solve mode=snapshot'
            self.dssCapacitors.Next
            dict_caps.update({list_caps[i]:desvio_cap[i]})


    # Caso do elemento ativo ser um transformador:
        self.dssTransformers.First
        global list_trafos
        list_trafos = [] #vai me mostrar o transformador
        for i in range(self.dssTransformers.Count):
            list_trafos.append(self.dssCktElement.Name)
            self.dssTransformers.Next

        global list_all_equipments
        list_all_equipments = list_caps + list_trafos
        
        # Seleciona o primeiro
        self.dssTransformers.First
        Vi = objeto.get_AllBusVmagPu()
        Vin = list(Vi)
        id_tensao = Vin[id_barra] #essa é a variável que a gente analisa desde o início.

        for i in range(self.dssTransformers.Count):
            desvio_tap_max = []
            desvio_tap_min = []
            print("\nA tensão que precisa ser analisada é {}".format(id_tensao))
            print("A barra que precisa ser analisada é {}".format(objeto.ativa_barra(list_buses[id_barra])))
            print("\nElemento selecionado: " + self.dssCktElement.Name)
            num_taps = self.dssTransformers.NumTaps/2
            num_taps = int(num_taps)

            global tap_inicial
            tap_inicial = self.dssTransformers.Tap
            print(tap_inicial) #ele não deve voltar para 1.1
            print(dict_trafos) #fazer uma condição que compare esses dois valores. Eles precisam estar iguais!
            global taps_trafos
            taps_trafos = list(dict_trafos.values()) #essa lista precisa ser atualizada
            print(taps_trafos)
            if n_iteracoes > 1:
                if tap_inicial is not taps_trafos[i]: #imprime só o nome do transformador.
                    tap_inicial = taps_trafos[i]
                    self.dssTransformers.Tap = tap_inicial
                print(tap_inicial)
                print(self.dssTransformers.Tap)

            itera = 0 # critério de parada, só para não ficar eternamente no while
            VoltagesPerTrafos = []
            
            if id_tensao < 1.0:
                
                while self.dssTransformers.Tap < self.dssTransformers.MaxTap and itera < 40:   
                    itera += 1
                    self.dssTransformers.Tap += 0.00625
                    self.dssText.Command = 'solve mode=snapshot'
                    Vi = objeto.get_AllBusVmagPu()
                    Vin = list(Vi)
                    tensao_iter = Vin[id_barra] #essa é a variável que eu criei para realizar os desvios de tensao
                    tap_atual = self.dssTransformers.Tap
                    desvio = id_tensao - tensao_iter
                    desvio_tap_max.append(abs(desvio))
                    print("Valor atualizado do tap: " + str(tap_atual))
                    print("Valor atualizado da tensão: " + str(tensao_iter))
                    VoltagesPerTrafos.append(tensao_iter)

                     
                    if self.dssTransformers.Tap == self.dssTransformers.MaxTap:
                        self.dssTransformers.Tap = 1.0
                        self.dssText.Command = 'solve mode=snapshot'
                        dict_trafos.update({list_trafos[i]:tap_inicial}) #precisa voltar para a posição inicial
                        break
                   
                # Imprimindo o desvio das tensões em cada tap em cada transformador e sua respectiva média:
                if desvio_tap_max == []:
                    media_desvio = math.nan
                else:
                    media_desvio = sum(desvio_tap_max)/len(desvio_tap_max)

                desvio_trafos.append(media_desvio)
                dict_allVoltages_trafos.update({list_trafos[i]:VoltagesPerTrafos})
                dict_trafos.update({list_trafos[i]:tap_inicial})

            elif 1.0 < id_tensao:

                while self.dssTransformers.Tap > self.dssTransformers.MinTap and itera < 40:
                    itera += 1
                    self.dssTransformers.Tap = self.dssTransformers.Tap - 0.00625   
                    self.dssText.Command = 'solve mode=snapshot'
                    Vi = objeto.get_AllBusVmagPu()
                    Vin = list(Vi)
                    tensao_iter = Vin[id_barra]
                    tap_atual = self.dssTransformers.Tap
                    desvio = id_tensao - tensao_iter
                    desvio_tap_min.append(abs(desvio))
                    print("Valor atualizado do tap: " + str(tap_atual))
                    print("Valor atualizado da tensão: " + str(tensao_iter))
                    VoltagesPerTrafos.append(tensao_iter)
                   

                    if self.dssTransformers.Tap == self.dssTransformers.MinTap:
                            self.dssTransformers.Tap = 1.0
                            self.dssText.Command = 'solve mode=snapshot'
                            dict_trafos.update({list_trafos[i]:tap_inicial})
                            break

                # Imprimindo o desvio das tensões em cada tap em cada transformador e sua respectiva média:        
                if desvio_tap_min == []: #arrumar isso
                    media_desvio_min = math.nan
                else:
                    media_desvio_min = sum(desvio_tap_min)/len(desvio_tap_min)
                              
                print(media_desvio_min)
                desvio_trafos.append(media_desvio_min)
                dict_allVoltages_trafos.update({list_trafos[i]:VoltagesPerTrafos})
                dict_trafos.update({list_trafos[i]:tap_inicial})
                print("\n") 
            self.dssTransformers.Next

        desvios_equip = desvio_cap + desvio_trafos
        print("Desvios totais: {}".format(desvios_equip))

        max_media = np.nanmax(desvios_equip)
        
        effectiveness = desvios_equip/max_media
        for i in range(len(effectiveness)):
            if math.isnan(effectiveness[i]):
                effectiveness[i] = -1
        print(type(effectiveness))
        global array_effectiveness
        array_effectiveness = array('d', effectiveness)
        print(array_effectiveness)
        
        print(dict_trafos)
        taps_trafos = list(dict_trafos.values())
        global equipamentos
        equipamentos = self.dssCapacitors.AllNames + self.dssTransformers.AllNames
       
        for i in range(len(array_effectiveness)):
            effectiveness = list(effectiveness)
            if array_effectiveness[i] == np.nanmax(array_effectiveness):
                print("O equipamento {} apresenta efetividade {}".format(i,array_effectiveness[i]))
            else:
                print("O equipamento {} apresenta efetividade {}".format(i,array_effectiveness[i]))

            global max_effectiveness
            max_effectiveness = np.nanmax(effectiveness)

        print("\n")        
        global intern_commutations
        global max_comutacoes
        intern_commutations = 0
        intern_commutations = float(intern_commutations)
        
        if n_iteracoes == 1:
            #pdb.set_trace()
            for i in range(len(list_caps)):
                #n_commutations.append(intern_commutations) #aqui ele zera todas as comutações. É para deixar zerado os que ainda não foram analisados
                commutations_capacitor.append(intern_commutations)
            for i in range(len(list_trafos)):
                commutations_trafo.append(intern_commutations)
        n_commutations = commutations_capacitor + commutations_trafo
        global array_n_commutations

        if n_iteracoes > 1: 
            #pdb.set_trace()
            if len(equip_analisado) > 1:
                for j in range(len(real_equip_analisado)):
                    #print(equip_analisado)
                    intern_commutations = 0
                    altera_commutations = intern_commutations + daily_commutations #a comutação diária estará com o valor correspondente da iteração anterior
                    n_commutations[real_equip_analisado[j]] = altera_commutations
            else:
                for j in range(len(equip_analisado)):
                    #print(equip_analisado)
                    intern_commutations = 0
                    altera_commutations = intern_commutations + daily_commutations #a comutação diária estará com o valor correspondente da iteração anterior
                    n_commutations[equip_analisado[j]] = altera_commutations
            flatten_equip_analisado = list(itertools.chain.from_iterable(list_equip_analisado)) #apenas peguei o "list_equip_analisado", que era uma lista de lista, e transformei para uma lista

        max_comutacoes = max(n_commutations)
        array_n_commutations = numpy.array(n_commutations)
        array_n_commutations_capacitor = numpy.array(commutations_capacitor)
        array_n_commutations_trafo = numpy.array(commutations_trafo)
        for i in range(len(list_caps)):
            valor = array_n_commutations_capacitor[i]/max_comutacoes
            commutactiveness_capacitor.append(valor)
            print("O capacitor {} apresenta comutatividade {}".format(i,commutactiveness_capacitor[i]))

        for i in range(len(list_trafos)):
            valor = array_n_commutations_trafo[i]/max_comutacoes
            commutactiveness_trafo.append(valor)
            print("O transformador {} apresenta comutatividade {}".format(i,commutactiveness_trafo[i]))

        for i in range(len(equipamentos)):
            valor = array_n_commutations[i]/max_comutacoes
            commutactiveness.append(valor)

        return effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, dict_allVoltages_trafos, tap_inicial, max_desvio, val_tensoes, commutactiveness, commutactiveness_capacitor, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido

    def cap_atuacao(self, effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, tap_inicial, commutactiveness, commutactiveness_capacitor, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido):

        # Etapa 2: encontrar equipamento de ajuste mais adequado considerando sua efetividade e quantidade de comutações
        
        #Criação das variáveis do problema
        efetividade = ctrl.Antecedent(np.arange(-1, 1.1, 0.1), 'efetividade') #configuração boa, loop na iter. 44
        comutatividade = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'comutatividade')
        cap_atuacao = ctrl.Consequent(np.arange(-1, 1.1, 0.1), 'capacidade de atuacao')
        
        #Criação do mapeamento da efetividade usando fç de pertinência trapezoidal:        
        efetividade['Low'] = fuzz.trapmf(efetividade.universe, [-1, -1, -0.9, -0.7])
        efetividade['Medium Low'] = fuzz.trapmf(efetividade.universe, [-0.8, -0.6, -0.4, -0.2])
        efetividade['Medium'] = fuzz.trapmf(efetividade.universe, [-0.3, -0.1, 0.1, 0.3])
        efetividade['Medium High'] = fuzz.trapmf(efetividade.universe, [0.2, 0.4, 0.6, 0.8])
        efetividade['High'] = fuzz.trapmf(efetividade.universe, [0.7, 0.9, 1, 1])
        
        #Criação do mapeamento da comutatividade usando fç de pertinência trapezoidal:        
        comutatividade['Low'] = fuzz.trapmf(comutatividade.universe, [0, 0, 0.05, 0.15])
        comutatividade['Medium Low'] = fuzz.trapmf(comutatividade.universe, [0.1, 0.2, 0.3, 0.4])
        comutatividade['Medium'] = fuzz.trapmf(comutatividade.universe, [0.35, 0.45, 0.55, 0.65])
        comutatividade['Medium High'] = fuzz.trapmf(comutatividade.universe, [0.6, 0.7, 0.8, 0.9])
        comutatividade['High'] = fuzz.trapmf(comutatividade.universe, [0.85, 0.95, 1, 1])

        #Criação do mapeamento da capacidade de atuação usando fç de pertinência trapezoidal:
        cap_atuacao['Low'] = fuzz.trapmf(cap_atuacao.universe, [-1, -1, -0.9, -0.7])
        cap_atuacao['Medium Low'] = fuzz.trapmf(cap_atuacao.universe, [-0.8, -0.6, -0.4, -0.2])
        cap_atuacao['Medium'] = fuzz.trapmf(cap_atuacao.universe, [-0.3, -0.1, 0.1, 0.3])
        cap_atuacao['Medium High'] = fuzz.trapmf(cap_atuacao.universe, [0.2, 0.4, 0.6, 0.8])
        cap_atuacao['High'] = fuzz.trapmf(cap_atuacao.universe, [0.7, 0.9, 1, 1])

        
        #CRIAÇÃO DAS REGRAS DE DECISÃO:
      
        #Capacidade de atuação = Low
        rule0 = ctrl.Rule(efetividade['Low'] & comutatividade['Medium Low'], cap_atuacao['Low'])        
        rule1 = ctrl.Rule(efetividade['Low'] & comutatividade['Medium'], cap_atuacao['Low'])      
        rule2 = ctrl.Rule(efetividade['Low'] & comutatividade['Medium High'], cap_atuacao['Low'])                                             
        rule3 = ctrl.Rule(efetividade['Low'] & comutatividade['High'], cap_atuacao['Low'])                                        
        rule4 = ctrl.Rule(efetividade['Medium Low'] & comutatividade['Medium High'], cap_atuacao['Low'])                                               
        rule5 = ctrl.Rule(efetividade['Medium Low'] & comutatividade['High'], cap_atuacao['Low'])                                 
        rule6 = ctrl.Rule(efetividade['Medium'] & comutatividade['High'], cap_atuacao['Low'])                                        
        rule7 = ctrl.Rule(efetividade['Medium High'] & comutatividade['High'], cap_atuacao['Low'])                                            
        
        #Capacidade de atuação = Medium Low
        rule8 = ctrl.Rule(efetividade['Medium'] & comutatividade['Medium'], cap_atuacao['Medium Low'])          
        rule9 = ctrl.Rule(efetividade['Medium Low'] & comutatividade['Medium Low'], cap_atuacao['Medium Low'])              
        rule10 = ctrl.Rule(efetividade['Medium Low'] & comutatividade['Medium'], cap_atuacao['Medium Low'])                  
        rule11 = ctrl.Rule(efetividade['Medium'] & comutatividade['Medium High'], cap_atuacao['Medium Low'])                 
        rule12 = ctrl.Rule(efetividade['High'] & comutatividade['High'], cap_atuacao['Medium Low'])                          
        rule13 = ctrl.Rule(efetividade['Medium High'] & comutatividade['Medium High'], cap_atuacao['Medium Low']) 
        
        #Capacidade de atuação = Medium
        rule14 = ctrl.Rule(efetividade['Low'] & comutatividade['Low'], cap_atuacao['Medium'])            
        rule15 = ctrl.Rule(efetividade['Medium Low'] & comutatividade['Low'], cap_atuacao['Medium'])                 
        rule16 = ctrl.Rule(efetividade['Medium High'] & comutatividade['Medium'], cap_atuacao['Medium'])             
        rule17 = ctrl.Rule(efetividade['Medium'] & comutatividade['Medium Low'], cap_atuacao['Medium'])              
        rule18 = ctrl.Rule(efetividade['High'] & comutatividade['Medium High'], cap_atuacao['Medium']) 
                  
        #Capacidade de atuação = Medium High
        rule19 = ctrl.Rule(efetividade['Medium'] & comutatividade['Low'], cap_atuacao['Medium High'])     
        rule20 = ctrl.Rule(efetividade['Medium High'] & comutatividade['Medium Low'], cap_atuacao['Medium High'])
           
        #Capacidade de atuação = High
        rule21 = ctrl.Rule(efetividade['High'] & comutatividade['Low'], cap_atuacao['High'])       
        rule22 = ctrl.Rule(efetividade['High'] & comutatividade['Medium Low'], cap_atuacao['High'])            
        rule23 = ctrl.Rule(efetividade['High'] & comutatividade['Medium'], cap_atuacao['High'])                
        rule24 = ctrl.Rule(efetividade['Medium High'] & comutatividade['Low'], cap_atuacao['High'])
        
        #Criando as regras de decisão da lógica
        atuacao = ctrl.ControlSystem([rule0 , rule1 , rule2 , rule3 , rule4 ,
                                      rule5 , rule6 , rule7 , rule8 , rule9 ,
                                      rule10, rule11, rule12, rule13, rule14,
                                      rule15, rule16, rule17, rule18, rule19,
                                      rule20, rule21, rule22, rule23, rule24])

        #investigar melhor o que isso faz:
        atuacao_simulador = ctrl.ControlSystemSimulation(atuacao)

        #COMPUTANDO OS RESULTADOS:
        atuacao_list = []
        atuacao_list_cap = []
        atuacao_list_trafo = []
        global equip_analisado
        equip_analisado = []
        print("\n")
        global equipments_name
        equipments_name = [i.split('.')[0] for i in list_all_equipments]

        for i in range(len(array_effectiveness)):
            atuacao_simulador.input['efetividade'] = array_effectiveness[i]
            atuacao_simulador.input['comutatividade'] = commutactiveness[i]

            #Computando o resultado
            atuacao_simulador.compute()
            atuacao_list.append(atuacao_simulador.output['capacidade de atuacao'])
            if atuacao_list[i] > 1.0:
                pdb.set_trace()
                atuacao_list[i] = atuacao_list[i] - 1
            #print(atuacao_list)
            if equipments_name.index('Capacitor') < 2: #tentar encontrar uma forma de deixar isso mais genérico
                print("Capacidade de atuação do equipamento {} é de {}".format(equipments_name[i],atuacao_list[i]))
            elif equipments_name.index('Transformer') >= 2:
                print("Capacidade de atuação do equipamento {} é de {}".format(equipments_name[i],atuacao_list[i]))
        
        atuacao_list_cap = atuacao_list[0:2] #tentar fazer algo genérico.
        atuacao_list_trafo = atuacao_list[2:10]
        effectiveness_trafo = effectiveness[2:10]
        print("\n")
        global highest_effectiveness
        highest_effectiveness = []
        for i in range(len(atuacao_list)):
            if atuacao_list[i] == max(atuacao_list):
                highest_effectiveness.append(effectiveness[i])

        print(tap_inicial)
        global trafo_eleito
        trafo_eleito = []
        if penalizado >= 1: 
            if (list(dict_trafos.values())[equip_ajustar] == self.dssTransformers.MaxTap and id_tensao < 0.94) or (list(dict_trafos.values())[equip_ajustar] == self.dssTransformers.MinTap and id_tensao > 1.05):
                for i in range(len(atuacao_list_trafo)):
                    if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                        print("O equipamento (transformador) {} é o escolhido para corrigir a tensão e terá o acréscimo de uma comutação".format(i)) #arrumar isso, está saindo o valor diferente
                for j in range(len(equip_penalizado)):           
                            atuacao_list_trafo[equip_penalizado[j]] = -1 #eliminaos o equipamento provisoriamente para que seja possível pegar o 2° maior
            
                for i in range(len(atuacao_list_trafo)):
                    if atuacao_list_trafo.count(max(atuacao_list_trafo)) > 1:
                        real_equip_analisado = []
                        highest_effectiveness = []
                        for i in range(len(atuacao_list_trafo)):
                            if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                                highest_effectiveness.append(effectiveness_trafo[i])
                        for i in range(len(atuacao_list_trafo)):
                            if effectiveness_trafo[i] == max(highest_effectiveness): #and (0.9 < taps_trafos[i] < 1.1):
                                print("Agora, o equipamento (transformador) {} é o escolhido, pois o outro equipamento não será útil.".format(i)) #aqui precisa ser o trafo 4
                                equip_analisado.append(i)
                        break
                    else:
                        if atuacao_list_trafo[i] == max(atuacao_list_trafo): #and (0.9 < taps_trafos[i] < 1.1): #dependendo da tensão que está se analisando, pode não funcionar
                            print("Agora, o equipamento (transformador) {} é o escolhido, pois o outro equipamento não será útil.".format(i))
                            equip_analisado.append(i) #adicionar o equipamento na lista, será enviado para a cap. de atuação
                                        
            else:
                print("O equipamento {} é o escolhido para corrigir a tensão e terá o acréscimo de uma comutação".format(equip_ajustar))
                equip_analisado.append(equip_ajustar)

        else:
            for i in range(len(atuacao_list)):
                if atuacao_list[i] == max(atuacao_list):
                        print("O equipamento (capacitores e transformadores) {} é o escolhido para corrigir a tensão e terá o acréscimo de uma comutação".format(i))
                        equip_analisado.append(i)
        
        print("Equip analisado: {}".format(equip_analisado))
        print(id_tensao)
        print("self.dssTransformers.Tap: {}".format(self.dssTransformers.Tap))
        global equip_select
        global test_equip_analisado
        global test_cap_analisado
        test_equip_analisado = []
        test_cap_analisado = []

        if penalizado >= 1: #aqui está certo
            for i in range(len(penalizado_real_escolhido)):
                print("\nEste será o número do equipamento (transformadores) a ser analisado: {}".format(penalizado_real_escolhido[i]))
                #equip_select: da o numero do equipamento relacionado aos trafos e capacitores
                equip_select = penalizado_real_escolhido[i] + len(atuacao_list) - len(atuacao_list_trafo) #isso aqui que eu coloquei afeta na aplicação da função comutatividade.
                if equip_analisado == []:
                    equip_analisado.append(equip_select)
        else:
            for i in range(len(effectiveness)):
                if effectiveness[i] == max(highest_effectiveness):
                    print("\nEste será o número do equipamento (capacitores e transformadores) a ser analisado: {}".format(i))
                    equip_select = i
                    print(equip_select)
                    real_equip = equip_select - len(atuacao_list) + len(atuacao_list_trafo)
                    test_equip_analisado.append(real_equip)
                    test_cap_analisado.append(equip_select)
                    global equip_select_list
                    equip_select_list = []
                    equip_select_list.append(equip_select)
                    if equip_analisado == []:
                        equip_analisado.append(equip_select)
                    print("Equipamento selecionado (capacitores e transformadores): {}".format(equip_analisado))
        print("\n")            
           
        return efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, tap_inicial, atuacao_list_trafo, atuacao_list_cap, equip_ajustar, penalizado, penalizado_real_escolhido

    def comutatividade_trafos(self, effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, vi_analisada, dict_allVoltages_trafos, tap_inicial, max_desvio, val_tensoes, atuacao_list_trafo, commutactiveness, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido):
        print("\n ---------------- COMUTATIVIDADE TRANSFORMADORES --------------------\n")
        # 1° passo: criar um loop que percorra todos os equipamentos, da mesma forma que a efetividade.
        penalizado = 0
        print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))
        global trafos_commutations
        trafos_commutations = {} 
        global analisado_trafo
        analisado_trafo = []
        global tensao_iter
        global tap_atual
        effectiveness_trafo = effectiveness[2:10] #arrumar isso
        highest_effectiveness = []

        for i in range(len(atuacao_list_trafo)): #apenas para selecionar os equipamentos adequados
            if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                analisado_trafo.append(i)

        global effect_equip
        global real_equip_analisado
        effect_equip = []
        real_equip_analisado = []
        global iter_equip_analisado
        #tem a função de pegar apenas 1 equipamento, caso exista mais de um, baseando-se no maior valor da efetividade. Também é criado o equipamento para ser feito a adição no n° de comutações
        if len(equip_analisado) > 1:
            iter_equip_analisado += 1
            for i in range(len(equip_analisado)):
                effect_equip.append(effectiveness[equip_analisado[i]]) #está pegando as efetividades dos equipamentos analisados

            for i in range(len(effectiveness_trafo)):
                if max(effect_equip) == effectiveness_trafo[i]:
                    real_equip_analisado.append(i)
                    print(real_equip_analisado)
                    print("Na verdade o equipamento (transformador) {} será o escolhido, pois apresenta uma efetividade maior".format(i))

        for i in range(len(atuacao_list_trafo)): #isso aqui é algo repetido?
            if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                highest_effectiveness.append(effectiveness_trafo[i]) #está pegando as efetividades dos equipamentos que possuem máxima cap. de atuação

        for i in range(len(list_trafos)): #trabalhar nisso
            if list_all_equipments[equip_select] == list_trafos[i]:
                equip_select_trafo = equip_select - len(atuacao_list) + len(atuacao_list_trafo)
                select_trafo = equip_select_trafo
                print("O equipamento (transformador) {} corresponde ao {}, que será usado nesta iteração".format(equip_select_trafo,list_trafos[i]))
                print(atuacao_list[equip_select])
            if equip_analisado == []:
                    equip_analisado.append(select_trafo)
        
        if len(equip_analisado) > 1:
            print("\nEntramos no outo if!\n")
            if atuacao_list[equip_select] == max(atuacao_list):
                        tap_inicial = self.dssTransformers.Tap
                        print("Teste 1: {}".format(tap_inicial))
                        taps_trafos = list(dict_trafos.values())
                        if n_iteracoes >= 1:
                            if tap_inicial is not taps_trafos[select_trafo]: #imprime só o nome do transformador.
                                tap_inicial = taps_trafos[select_trafo]
                                self.dssTransformers.Tap = tap_inicial
                            print(tap_inicial)
                            print(self.dssTransformers.Tap)
                        print(id_tensao)
                        #self.dssTransformers.First
                        for j in range(len(list_trafos)):
                            if effectiveness_trafo[j] == max(highest_effectiveness): #se esse equip for o mais efetivo.
                                print("\nElemento Ativo: {}".format(objeto.ativa_elemento(list_trafos[j])))
                                break
                         #   self.dssTransformers.Next
                        for j in range(len(list_buses)):
                            if id_barra == j:
                                print("Barra Ativa: {}".format(objeto.ativa_barra(list_buses[j])))
                                break

                        if tap_inicial == self.dssTransformers.MaxTap and id_tensao < 0.94:
                            print("O equipamento selecionado não pode resolver o problema da tensão. Procure outro equipamento\n")
                            penalizado += 1
                            
                        elif tap_inicial == self.dssTransformers.MinTap and id_tensao > 1.05:
                            print("O equipamento selecionado não pode resolver o problema da tensão. Procure outro equipamento\n")
                            penalizado += 1
                        
                        else:
                            global num_cond
                            if id_tensao > 0.94 and id_tensao < 1.05:
                                num_cond += 1
                                tensao_iter = id_tensao #pois tensao_iter estará com um valor da outra iteração
                            allVoltages_trafo = list(dict_allVoltages_trafos[list_trafos[i]])
                            print("self.dssTransformers.Tap: {}".format(self.dssTransformers.Tap))
                            if id_tensao < 0.94: #coloquei dessa forma pois se fizer id_tensao < 1, pegará valores que estão dentro dos limites aceitáveis
                                    while self.dssTransformers.Tap < self.dssTransformers.MaxTap:                                        
                                        self.dssTransformers.Tap += 0.00625
                                        self.dssText.Command = 'solve mode=snapshot' # isso não pode ser tirado, do outro jeito não deu certo.
                                        Vi = objeto.get_AllBusVmagPu()
                                        Vin = list(Vi)
                                        tensao_iter = Vin[id_barra]
                                        tap_atual = self.dssTransformers.Tap
                                        print(tap_atual)
                                        print(tensao_iter)
                    
                                        if self.dssTransformers.Tap == self.dssTransformers.MaxTap or (tensao_iter > 0.94 and tensao_iter < 1.05): #colocar essa faixa pequena para que ela não passe de 1.05
                                            for i in range(len(real_equip_analisado)):
                                                print("\nElemento selecionado: " + str(list_trafos[real_equip_analisado[i]]))
                                                print("Valor atualizado do tap: " + str(tap_atual))
                                                print("Valor atualizado da tensão: " + str(tensao_iter))
                                                dict_trafos.update({list_trafos[real_equip_analisado[i]]:tap_atual})
                                            break
                            elif 1.05 < id_tensao:
                                list_tensao_tap = []
                                print(iterBus_violated)
                                iter = 0
                                while self.dssTransformers.Tap > self.dssTransformers.MinTap:
                                    iter += 1
                                    self.dssTransformers.Tap = self.dssTransformers.Tap - 0.00625
                                    self.dssText.Command = 'solve mode=snapshot'
                                    Vi = objeto.get_AllBusVmagPu()
                                    Vin = list(Vi)
                                    tensao_iter = Vin[id_barra]
                                    tap_atual = self.dssTransformers.Tap    
                                    print(tap_atual)
                                    print(tensao_iter)

                                    if self.dssTransformers.Tap == self.dssTransformers.MinTap or (tensao_iter > 0.94 and tensao_iter < 1.05): #or len(tensao_tap_iter) !=0:
                                            for i in range(len(real_equip_analisado)):
                                                print("\nElemento selecionado: " + str(list_trafos[real_equip_analisado[i]])) #arrumar isso aqui
                                                print("Valor atualizado do tap: " + str(tap_atual))
                                                print("Valor atualizado da tensão: " + str(tensao_iter))                                   
                                                dict_trafos.update({list_trafos[real_equip_analisado[i]]:tap_atual})
                                            break

                            print("Verificar se os taps estão corretos:\n {}".format(dict_trafos))
                            global daily_commutations
                            global altera_commutations
                            global max_comutacoes
                            global list_equip_analisado
                
                            intern_commutations = 0

                        # ARMAZENANDO AS COMUTAÇÕES NOS RESPECTIVOS EQUIPAMENTOS:
                            if id_tensao < 0.94 or id_tensao > 1.05:
                                for i in range(len(list_equip_analisado)):
                                    for j in range(len(real_equip_analisado)):
                                        if list_equip_analisado[i] != list_equip_analisado[i-1]: #se o equipamento for igual ao da iteração anterior, então a comutação diária não é zerada
                                            daily_commutations = 0
                                            trafos_commutations.update({list_trafos[real_equip_analisado[j]]:daily_commutations})
                    
                                for j in range(len(real_equip_analisado)):
                                    if real_equip_analisado in list_equip_analisado: 
                                        intern_commutations = list_equip_analisado.count(real_equip_analisado)  #conta o número de vezes que o equipamento aparece para ser analisado              
                                    else:
                                        intern_commutations = 1

                                    altera_commutations = intern_commutations + daily_commutations
                                    commutations_trafo[real_equip_analisado[j]] = altera_commutations

                                max_comutacoes = max(commutations_trafo)
                                for j in range(len(real_equip_analisado)):
                                    trafos_commutations.update({list_trafos[real_equip_analisado[j]]:altera_commutations})
               
                                print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                                print("Número de comutações internas: {}".format(intern_commutations))

                                #Atualizando a comutatividade:
                                print("\nAtualizando a comutatividade:\n")
                                for i in range(len(list_trafos)):
                                    valor = commutations_trafo[i]/max_comutacoes
                                    commutactiveness_trafo[i] = valor
                                    print("O transformador {} apresenta comutatividade {}".format(list_trafos[i],commutactiveness_trafo[i]))
                                print(commutations_trafo)
                                n_commutations = commutations_capacitor + commutations_trafo
                                print(n_commutations)
            
        else:
            equip_analisado[0] = select_trafo
            self.dssTransformers.First #tem alguma coisa a ver com isso o problema das tensões
            for i in range(len(atuacao_list_trafo)):
                    if (atuacao_list_trafo[i] == max(atuacao_list_trafo) and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(2,atuacao_list_trafo)[1] and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(3,atuacao_list_trafo)[2] and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(5,atuacao_list_trafo)[4] and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(6,atuacao_list_trafo)[5] and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(7,atuacao_list_trafo)[6] and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(8,atuacao_list_trafo)[7] and i == equip_select_trafo) or (atuacao_list_trafo[i] == heapq.nlargest(4,atuacao_list_trafo)[3] and i == equip_select_trafo):                        
                        tap_inicial = self.dssTransformers.Tap
                        print("Tap inicial antes do if: {}".format(tap_inicial))
                        taps_trafos = list(dict_trafos.values())
                        print("taps_trafos[i]: {}".format(taps_trafos[i]))
                        if n_iteracoes > 1:
                            if tap_inicial is not taps_trafos[i]: #imprime só o nome do transformador.
                                tap_inicial = taps_trafos[i]
                                self.dssTransformers.Tap = tap_inicial
                            print("Tap inicial depois do if: {}".format(tap_inicial))
                            print("self.dssTransformers.Tap: {}".format(self.dssTransformers.Tap))

                        print("\nElemento Ativo: {}".format(objeto.ativa_elemento(list_trafos[i])))
                        for j in range(len(list_buses)):
                            if id_barra == j:
                                print("Barra Ativa: {}".format(objeto.ativa_barra(list_buses[j])))
                                break

                        if tap_inicial == self.dssTransformers.MaxTap and id_tensao < 0.94:
                            print("O equipamento selecionado não pode resolver o problema da tensão. Procure outro equipamento\n")
                            penalizado += 1
                            break
                        elif tap_inicial == self.dssTransformers.MinTap and id_tensao > 1.05:
                            print("O equipamento selecionado não pode resolver o problema da tensão. Procure outro equipamento\n")
                            penalizado += 1
                            break
    
                        if id_tensao > 0.94 and id_tensao < 1.05:
                            num_cond += 1
                            tensao_iter = id_tensao #pois tensao_tap estará com um valor da outra iteração
                            print(tensao_iter)
                        allVoltages_trafo = list(dict_allVoltages_trafos[list_trafos[i]])
                        print("self.dssTransformers.Tap: {}".format(self.dssTransformers.Tap))
                        if id_tensao < 0.94: #coloquei dessa forma pois se fizer id_tensao < 1, pegará valores que estão dentro dos limites aceitáveis

                                while self.dssTransformers.Tap < self.dssTransformers.MaxTap:
                                    self.dssTransformers.Tap += 0.00625
                                    self.dssText.Command = 'solve mode=snapshot' # isso não pode ser tirado, do outro jeito não deu certo.
                                    Vi = objeto.get_AllBusVmagPu()
                                    Vin = list(Vi)
                                    tensao_iter = Vin[id_barra]
                                    tap_atual = self.dssTransformers.Tap
                                    print(tap_atual)
                                    print(tensao_iter)
                    
                                    if self.dssTransformers.Tap == self.dssTransformers.MaxTap or (tensao_iter > 0.94 and tensao_iter < 1.05): #colocar essa faixa pequena para que ela não passe de 1.05
                                        for i in range(len(equip_analisado)):
                                            print("\nElemento selecionado: " + str(list_trafos[equip_analisado[i]]))
                                            print("Valor atualizado do tap: " + str(tap_atual))
                                            print("Valor atualizado da tensão: " + str(tensao_iter))
                                            dict_trafos.update({list_trafos[select_trafo]:tap_atual})
                                        break

                        elif 1.05 < id_tensao:
                            list_tensao_tap = []
                            print(iterBus_violated)
                            iter = 0
                            while self.dssTransformers.Tap > self.dssTransformers.MinTap:
                                iter += 1
                                self.dssTransformers.Tap = self.dssTransformers.Tap - 0.00625
                                self.dssText.Command = 'solve mode=snapshot'
                                Vi = objeto.get_AllBusVmagPu()
                                Vin = list(Vi)
                                tensao_iter = Vin[id_barra]
                                tap_atual = self.dssTransformers.Tap    
                                print(tap_atual)
                                print(tensao_iter)

                                if self.dssTransformers.Tap == self.dssTransformers.MinTap or (tensao_iter > 0.94 and tensao_iter < 1.05): #or len(tensao_tap_iter) !=0:
                                        for i in range(len(equip_analisado)):
                                            print("\nElemento selecionado: " + str(list_trafos[equip_analisado[i]]))
                                            print("Valor atualizado do tap: " + str(tap_atual))
                                            print("Valor atualizado da tensão: " + str(tensao_iter))                                   
                                            dict_trafos.update({list_trafos[select_trafo]:tap_atual})
                                        break

                        print("Verificar se os taps estão corretos:\n {}".format(dict_trafos))
                        intern_commutations = 0

                    # ARMAZENANDO AS COMUTAÇÕES NOS RESPECTIVOS EQUIPAMENTOS:
                        if id_tensao < 0.94 or id_tensao > 1.05:
                            for i in range(len(list_equip_analisado)):
                                for j in range(len(equip_analisado)):
                                    if list_equip_analisado[i] != list_equip_analisado[i-1]: #se o equipamento for igual ao da iteração anterior, então a comutação diária não é zerada
                                        daily_commutations = 0
                                        trafos_commutations.update({list_trafos[equip_analisado[j]]:daily_commutations})

                            for j in range(len(equip_analisado)):
                                if equip_analisado in list_equip_analisado: 
                                    intern_commutations = list_equip_analisado.count(equip_analisado)  #conta o número de vezes que o equipamento aparece para ser analisado              
                                else:
                                    intern_commutations = 1

                                altera_commutations = intern_commutations + daily_commutations
                                commutations_trafo[equip_analisado[j]] = altera_commutations
                        
                            max_comutacoes = max(commutations_trafo)
                            for j in range(len(equip_analisado)):
                                trafos_commutations.update({list_trafos[equip_analisado[j]]:altera_commutations})
               
                            print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                            print("Número de comutações internas: {}".format(intern_commutations))

                            #Atualizando a comutatividade:
                            print("\nAtualizando a comutatividade:\n")
                            for i in range(len(list_trafos)):
                                valor = commutations_trafo[i]/max_comutacoes
                                commutactiveness_trafo[i] = valor
                                print("O transformador {} apresenta comutatividade {}".format(list_trafos[i],commutactiveness_trafo[i]))
                            print(commutations_trafo)
                            n_commutations = commutations_capacitor + commutations_trafo
                            print(n_commutations)        
                    self.dssTransformers.Next

        if penalizado >=1:
                
                self.dssTransformers.First
                for i in range(len(list_trafos)):
                    if atuacao_list_trafo[i] == max(atuacao_list_trafo) and i == select_trafo:
                        print("Elemento Ativo: {} \n".format(objeto.ativa_elemento(list_trafos[i])))
                        break
                    self.dssTransformers.Next

                #VERIFICAÇÃO DOS TAPS C/ VAR.DIFERENTES:
                print("tap_inicial: {}".format(tap_inicial))
                print("self.dssTransformers.Tap: {}".format(self.dssTransformers.Tap))

                if (tap_inicial == self.dssTransformers.MaxTap and id_tensao < 0.94) or (tap_inicial == self.dssTransformers.MinTap and id_tensao > 1.05):
                    equip_analisado = []
                    print("\nFunção Comutatividade:")
                    for i in range(len(effectiveness_trafo)):
                        if atuacao_list_trafo[i] == max(atuacao_list_trafo) and i == select_trafo:
                            equip_analisado.append(i) #pegamos o equipamento c/ maior capacidade de atuação, mas com o tap a 1.1 ou 0.9
                            equip_ajustar = i
                            equip_penalizado.append(i)
                            print(equip_penalizado)
                            print("taps_trafos[i] (esse é o valor que está sendo passado no if): {}".format(taps_trafos[i]))
                    print("\nO equipamento selecionado não resolverá o problema. Devemos pegar o 2° equipamento com maior capacidade de atuação.")
                    for k in range(len(atuacao_list_trafo)): #aqui está certo!
                        if (list(dict_trafos.values())[k] == self.dssTransformers.MaxTap and id_tensao < 0.94) or (list(dict_trafos.values())[k] == self.dssTransformers.MinTap and id_tensao > 1.05):
                            atuacao_list_trafo[k] = -1 

                    for i in range(len(atuacao_list_trafo)):
                        if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                            equip_analisado.append(i) #adicionar o equipamento na lista, será enviado para a cap. de atuação
                    if len(equip_analisado) > 1:
                        penalizado_real_escolhido = []
                        highest_effectiveness = []
                        for i in range(len(atuacao_list_trafo)):
                            if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                                highest_effectiveness.append(effectiveness_trafo[i])
                        for i in range(len(atuacao_list_trafo)):
                            if highest_effectiveness.count(max(highest_effectiveness)) == 1:
                                if effectiveness_trafo[i] == max(highest_effectiveness): #and (0.9 < taps_trafos[i] < 1.1):
                                    if n_iteracoes == 167:
                                        pdb.set_trace()
                                    print("O equipamento (transformador) {} é o escolhido para corrigir a tensão e terá o acréscimo de uma comutação".format(i))
                                    penalizado_real_escolhido.append(i) #precisa ser repassado para a fç capacidade de atuação
                            elif highest_effectiveness.count(max(highest_effectiveness)) > 1:
                                    if i == 0:
                                        print("O equipamento (transformador) {} é o escolhido para corrigir a tensão e terá o acréscimo de uma comutação".format(i))
                                        penalizado_real_escolhido.append(i) #precisa ser repassado para a fç capacidade de atuação
                   
                    else:
                        if atuacao_list_trafo[i] == max(atuacao_list_trafo):
                            print("O equipamento (transformador) {} é o escolhido para corrigir a tensão e terá o acréscimo de uma comutação".format(i))
                            equip_analisado.append(i)
                            print("Tap deste equipamento: {}".format(taps_trafos[i]))
                            print(equip_ajustar)
                        
        return n_commutations, tap_inicial, equip_ajustar, penalizado, penalizado_real_escolhido, equip_analisado, atuacao_list_trafo
        
    def comutatividade_capacitores(self, effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, vi_analisada, max_desvio, val_tensoes, atuacao_list_cap, commutactiveness, commutactiveness_capacitor):
            print("\n ---------------- COMUTATIVIDADE CAPACITORES --------------------\n")
            global analisado_capacitor
            global daily_commutations
            global altera_commutations
            global max_comutacoes
            global list_cap_analisado
            global tensao_iter
            caps_commutations = {}
            analisado_capacitor = []
            highest_effectiveness = []
            effectiveness_cap = effectiveness[0:2]
            for i in range(len(atuacao_list_cap)): #apenas para selecionar os equipamentos adequados
                if atuacao_list_cap[i] == max(atuacao_list_cap):
                    analisado_capacitor.append(i)

            global effect_equip
            global real_equip_analisado
            effect_equip = []
            real_equip_analisado = []
            global iter_equip_analisado
            if len(equip_analisado) > 1:
                iter_equip_analisado += 1
                for i in range(len(equip_analisado)):
                    effect_equip.append(effectiveness[equip_analisado[i]])
                
                for i in range(len(effectiveness_cap)):
                    if max(effect_equip) == effectiveness_cap[i]:
                        real_equip_analisado.append(i)
                        print(real_equip_analisado)
                        print("Na verdade o equipamento {} será o escolhido, pois apresenta uma efetividade maior".format(i))
            else:
                for i in range(len(equip_analisado)):
                    effect_equip.append(effectiveness[equip_analisado[i]])
                for i in range(len(effectiveness_cap)):
                    if max(effect_equip) == effectiveness_cap[i]:
                        real_equip_analisado.append(i)
                        print(real_equip_analisado)
                        print("Na verdade o equipamento {} será o escolhido, pois apresenta uma efetividade maior".format(i))

            for i in range(len(atuacao_list_cap)):
                if atuacao_list_cap[i] == max(atuacao_list_cap):
                    highest_effectiveness.append(effectiveness_cap[i])


            for i in range(len(effectiveness_cap)):
                if effectiveness_cap[i] == max(highest_effectiveness):
                    print("\nEste será o número do equipamento a ser analisado: {}".format(i))
                    global select_trafo
                    select_trafo = i
                    print(select_trafo)
                    if equip_analisado == []:
                        equip_analisado.append(select_trafo)
                    print("Equipamento selecionado: {}".format(select_trafo))
        

            for i in range(len(list_caps)): #trabalhar nisso
                if list_all_equipments[equip_select] == list_trafos[i]:
                    print("O equipamento {} corresponde ao {}, que será usado nesta iteração".format(select_trafo,list_trafos[i]))
                    print(atuacao_list[equip_select])



            self.dssCapacitors.First
            for i in range(self.dssCapacitors.Count):
                if atuacao_list_cap[i] == max(atuacao_list_cap):
                    
                    #print("Elemento selecionado: " + self.dssCktElement.Name) #está com o nome errado!
                    print("Elemento Ativo: {} \n".format(objeto.ativa_elemento(list_caps[i])))
                    print("Estado atual: {}".format(estados))
                    if estados == (1,):
                        #pdb.set_trace()
                        self.dssCapacitors.Open()
                    elif estados == (0,):
                        #pdb.set_trace()
                        self.dssCapacitors.Close()

                    self.dssText.Command = 'solve mode=snapshot'
                    if max_desvio == Vmin - min(val_tensoes):
                        Vi = objeto.get_AllBusVmagPu()
                        Vin = list(Vi)
                        tensao_iter = Vin[id_barra]
                        print("Tensão atualizada: " + str(tensao_iter))
                    elif max_desvio == max(val_tensoes) - Vmax:
                        Vi = objeto.get_AllBusVmagPu()
                        Vin = list(Vi)
                        tensao_iter = Vin[id_barra]
                        print("Tensão atualizada: " + str(tensao_iter))
                    print(estados)
                    self.dssText.Command = 'solve mode=snapshot'
                    self.dssCapacitors.Next
                

            # ARMAZENANDO AS COMUTAÇÕES NOS RESPECTIVOS EQUIPAMENTOS:
                    global intern_commutations
                    if id_tensao < 0.94 or id_tensao > 1.05:
                        
                        for i in range(len(list_cap_analisado)):
                            for j in range(len(real_equip_analisado)):
                                if list_cap_analisado[i] != list_cap_analisado[i-1]: #se o equipamento for igual ao da iteração anterior, então a comutação diária não é zerada
                                    daily_commutations = 0
                                    caps_commutations.update({list_caps[real_equip_analisado[j]]:daily_commutations})
                    
                        for j in range(len(real_equip_analisado)):
                            if real_equip_analisado in list_cap_analisado: 
                                intern_commutations = list_cap_analisado.count(real_equip_analisado)  #conta o número de vezes que o equipamento aparece para ser analisado              
                            else:
                                intern_commutations = 1

                            altera_commutations = intern_commutations + daily_commutations
                            commutations_capacitor[real_equip_analisado[j]] = altera_commutations
                        
                        max_comutacoes = max(commutations_capacitor)
                        for j in range(len(real_equip_analisado)):
                            caps_commutations.update({list_caps[real_equip_analisado[j]]:altera_commutations})
               
                        print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                        print("Número de comutações internas: {}".format(intern_commutations))

                        #Atualizando a comutatividade:
                        print("\nAtualizando a comutatividade:\n")
                        for i in range(len(list_caps)):
                            valor = commutations_capacitor[i]/max_comutacoes
                            commutactiveness_capacitor[i] = valor
                            print("O equipamento {} apresenta comutatividade {}".format(list_caps[i],commutactiveness_capacitor[i]))
                        print(commutations_capacitor)
                        n_commutations = commutations_capacitor + commutations_trafo
                        print(n_commutations)

                    return n_commutations, tap_inicial

if __name__ == "__main__":

        # Criar um objeto da classe dss
        objeto = DSS(r"C:\Users\gusta\OneDrive\Documentos\UFSC\LABSPOT\LABSPOT_20.1\Simulações\IEEE34Barras\ieee34Mod1.1.dss")

        print ("Versão do OpenDSS: " + objeto.versao_DSS() + "\n")

        # Resolver o fluxo de potência
        objeto.compile_DSS()
        objeto.solve_Pflow()
       
        # Informações dos valores das tensões em pu de todas as barras
        Vi = objeto.get_AllBusVmagPu()
        Vin = list(Vi)
        print("Tensões em todas as barras em pu: " + str(Vin) + " \n")
        global Vmax, Vmin
        Vmax = 1.05
        Vmin = 0.94
        #barras = objeto.get_nome_allbus()
        tam = len(Vin)
        list_buses = []
        list_equip_analisado = []
        list_cap_analisado = []
        global n_iteracoes
        n_iteracoes = 0
        daily_commutations = 0
        global flatten_equip_analisado
        #global max_comutacoes
        global commutactiveness_trafo 
        global commutactiveness_capacitor
        
        commutactiveness_trafo = []
        commutactiveness_capacitor = []
        vi_analisada = []
        global dict_trafos
        dict_trafos = {} #vai me mostrar o transformador e o tap atual
        global n_commutations
        n_commutations = [] #lista que armazena o número de comutações em cada equipamento
        global commutations_trafo, commutations_capacitor
        commutations_trafo = []
        commutations_capacitor = []
        global dict_allVoltages_trafos
        global list_allVoltages
        global VoltagesPerTrafos
        global iterBus_violated
        global list_all_bus_wrong
        global penalizado
        global penalizado_list
        list_all_bus_wrong = []
        num_cond = 0
        iter_equip_analisado = 0
        iter_tensoes = 0
        iter_teste = 0
        penalizado = 0
        global equip_penalizado
        for i in range(len(Vin)):
            
            while (Vin[i] < Vmin or Vin[i] > Vmax) or n_iteracoes < 300:
                commutactiveness = []
                tensao_iter = 0
                id_tensao = 0
                equip_penalizado = []
                iterBus_violated = 0
                n_iteracoes += 1
                print("Vmin: {}".format(Vmin))
                print("Vmax: {}".format(Vmax))
                print("\nNúmero de iterações do algoritmo: {}\n".format(n_iteracoes))
                print(dict_trafos)
                # Etapa 1: Identificação das barras violadas, efetividade dos equipamentos e sua comutatividade inicial
                print("\nEfetividade e comutação inicial:\n")
                effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, dict_allVoltages_trafos, tap_inicial, max_desvio, val_tensoes, commutactiveness, commutactiveness_capacitor, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido = objeto.efetividade()
                list_all_bus_wrong.append(all_bus_wrong)
                
                print("\nINFORMAÇÕES IMPORTANTES:\n")
                print("Iteração atual: {}\n".format(n_iteracoes))
                print("Menor número de barras violadas: {}".format(min(list_all_bus_wrong)))
                print("\nN° de barras violadas da iteração atual: {}".format(all_bus_wrong))
                print("Número de vezes que foi preciso utilizar a condição do id_tensao: {}".format(num_cond))
                print("Número de vezes que teve mais de 1 equipamento: {}".format(iter_equip_analisado))

                # Etapa 2: Utilização da lógica fuzzy para saber qual o equipamento será utilizado para o ajuste de tensão
                print("\nIncremento da lógica fuzzy:")
                efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, tap_inicial, atuacao_list_trafo, atuacao_list_cap, equip_ajustar, penalizado, penalizado_real_escolhido = objeto.cap_atuacao(effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, tap_inicial, commutactiveness, commutactiveness_capacitor, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido)
                if equip_select >= 0 and equip_select < 2:
                    if len(equip_analisado) > 1:
                        list_cap_analisado.append(test_cap_analisado)
                    else:
                        list_cap_analisado.append(equip_analisado) #só pega o primeiro equipamento que chega
                elif equip_select >= 2:
                    if len(equip_analisado) > 1:
                        list_equip_analisado.append(test_equip_analisado)
                    else:
                        list_equip_analisado.append(equip_analisado)
                print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))
                
                # Etapa 3: Adição no número de comutações na função comutatividade e alteração do tap do trafo especificado para realizar o ajuste
                print("\nAdição do número total de comutações :\n")
                
                if equip_select < 2:
                    n_commutations, tap_inicial = objeto.comutatividade_capacitores(effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, vi_analisada, max_desvio, val_tensoes, atuacao_list_cap, commutactiveness, commutactiveness_capacitor)
                else:
                    n_commutations, tap_inicial, equip_ajustar, penalizado, penalizado_real_escolhido, equip_analisado, atuacao_list_trafo = objeto.comutatividade_trafos(effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, vi_analisada, dict_allVoltages_trafos, tap_inicial, max_desvio, val_tensoes, atuacao_list_trafo, commutactiveness, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido)
                
                if tensao_iter > 0.94 and tensao_iter < 1.05:
                    print("\nTensão atualizada: {}".format(tensao_iter))
                    print("\nA tensão atingiu o nível adequado! Não se esqueça de pegar os equipamentos utilizados e adicionar +1 na comutação diária e zerar a comutação interna!\n")
                    
                    if len(equip_analisado) > 1:
                        if equip_select < 2:
                            for j in range(len(real_equip_analisado)):
                                intern_commutations = 0
                                if real_equip_analisado in list_cap_analisado: # não esquecer de alterar no outro também
                                    daily_commutations = list_cap_analisado.count(real_equip_analisado)                       
                                else:
                                    daily_commutations = 1
                                altera_commutations = intern_commutations + daily_commutations
                                n_commutations[real_equip_analisado[j]] = altera_commutations
                                max_comutacoes = max(n_commutations)
                        else:
                            for j in range(len(real_equip_analisado)):
                                intern_commutations = 0
                                if real_equip_analisado in list_equip_analisado: # não esquecer de alterar no outro também
                                    daily_commutations = list_equip_analisado.count(real_equip_analisado)                       
                                else:
                                    daily_commutations = 1
                                altera_commutations = intern_commutations + daily_commutations
                                n_commutations[real_equip_analisado[j]] = altera_commutations
                                max_comutacoes = max(n_commutations)
                        print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))
                        print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                        print("Número de comutações internas: {}".format(intern_commutations))

                    else:
                        if equip_select < 2:
                            for j in range(len(equip_analisado)):
                                intern_commutations = 0
                                if equip_analisado in list_cap_analisado: # não esquecer de alterar no outro também
                                    daily_commutations = list_cap_analisado.count(equip_analisado)                       
                                else:
                                    daily_commutations = 1
                                altera_commutations = intern_commutations + daily_commutations
                                n_commutations[equip_analisado[j]] = altera_commutations
                                max_comutacoes = max(n_commutations)
                        else:
                            for j in range(len(equip_analisado)):
                                intern_commutations = 0
                                if equip_analisado in list_equip_analisado: # não esquecer de alterar no outro também
                                    daily_commutations = list_equip_analisado.count(equip_analisado)                       
                                else:
                                    daily_commutations = 1
                                altera_commutations = intern_commutations + daily_commutations
                                n_commutations[equip_analisado[j]] = altera_commutations
                                max_comutacoes = max(n_commutations)
                        print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))
                        print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                        print("Número de comutações internas: {}".format(intern_commutations))
                    
                   
                else:
                    iterBus_violated = 0
                    while tensao_iter < 0.94 or tensao_iter > 1.05:
                        iterBus_violated += 1
                        print("\nTensão atualizada: {}".format(tensao_iter))
                        vi_analisada.append(tensao_iter)
                        print("\nA tensão ainda não atingiu o nível adequado. Por favor, procure outro equipamento e adicione +1 na comutação.\n")
                        print("\nProcura por novos equipamentos e adição na comutação:\n") 
                        objeto.solve_Pflow() #não resetou para o valor inicial (melhor)
                        Vi = objeto.get_AllBusVmagPu()
                        Vin = list(Vi)
                        tensao_teste = Vin[id_barra]
                        print("Barra selecionada: {}".format(id_barra))
                        id_tensao = tensao_iter
                        print("Tensao tap: {}".format(tensao_iter))
                        print("Id tensão: {}".format(id_tensao)) #se essa tensão atingir os níveis adequados, aí temos um problema.
                        print("Tensão teste: {}".format(tensao_teste))
                        desvio_tensoes = id_tensao - tensao_teste
                        if id_tensao != tensao_teste:
                            iter_tensoes += 1

                        print("\nNúmero de vezes que as tensões são diferentes: {}".format(iter_tensoes))
                        print("Vmin: {}".format(Vmin))
                        print("Vmax: {}".format(Vmax))
                        desvio_max = Vmax - Vmin
                        print(desvio_max)
                        print(abs(desvio_tensoes))
                        commutactiveness = commutactiveness_capacitor + commutactiveness_trafo

                        #Etapa 4: Entrando com as novas capacidades de atuação (lógica fuzzy):
                        print("\nEntrando com as novas capacidades de atuação (lógica fuzzy):\n")
                        efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, tap_inicial, atuacao_list_trafo, atuacao_list_cap, equip_ajustar, penalizado, penalizado_real_escolhido = objeto.cap_atuacao(effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, tap_inicial, commutactiveness, commutactiveness_capacitor, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido)
                        if equip_select >= 0 and equip_select < 2:
                            if len(equip_analisado) > 1:
                                list_cap_analisado.append(test_cap_analisado)
                            else:
                                list_cap_analisado.append(equip_analisado) #só pega o primeiro equipamento que chega
                        elif equip_select >= 2:
                            if len(equip_analisado) > 1:
                                list_equip_analisado.append(test_equip_analisado)
                            else:
                                list_equip_analisado.append(equip_analisado)
                        print(equip_analisado)
                        print(iter_equip_analisado)
                        if equip_select < 2:
                            n_commutations, tap_inicial = objeto.comutatividade_capacitores(effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, vi_analisada, max_desvio, val_tensoes, atuacao_list_cap, commutactiveness, commutactiveness_capacitor)
                        else:
                            n_commutations, tap_inicial, equip_ajustar, penalizado, penalizado_real_escolhido, equip_analisado, atuacao_list_trafo = objeto.comutatividade_trafos(effectiveness, max_effectiveness, id_tensao, n_commutations, num_taps, id_barra, Vmin, Vmax, efetividade, comutatividade, cap_atuacao, atuacao, atuacao_simulador, atuacao_list, equip_analisado, vi_analisada, dict_allVoltages_trafos, tap_inicial, max_desvio, val_tensoes, atuacao_list_trafo, commutactiveness, commutactiveness_trafo, equip_ajustar, penalizado, penalizado_real_escolhido)

                        print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))

                        if tensao_iter > 0.94 and tensao_iter < 1.05:
                            print("\nTensão atualizada: {}".format(tensao_iter))
                            print("\nA tensão atingiu o nível adequado! Não se esqueça de pegar os equipamentos utilizados e adicionar +1 na comutação diária e zerar a comutação interna!\n")
                    
                            #Zerando a comutação interna e adicionando o acréscimo na comutação diária:
                            if tensao_iter > 0.94 and tensao_iter < 1.05:
                                if len(equip_analisado) > 1:
                                    if equip_select < 2:
                                        for j in range(len(real_equip_analisado)):
                                            intern_commutations = 0
                                            if real_equip_analisado in list_cap_analisado: # não esquecer de alterar no outro também
                                                daily_commutations = list_cap_analisado.count(real_equip_analisado)                       
                                            else:
                                                daily_commutations = 1
                                            altera_commutations = intern_commutations + daily_commutations
                                            n_commutations[real_equip_analisado[j]] = altera_commutations
                                            max_comutacoes = max(n_commutations)
                                    else:
                                        for j in range(len(real_equip_analisado)):
                                            intern_commutations = 0
                                            if real_equip_analisado in list_equip_analisado: # não esquecer de alterar no outro também
                                                daily_commutations = list_equip_analisado.count(real_equip_analisado)                       
                                            else:
                                                daily_commutations = 1
                                            altera_commutations = intern_commutations + daily_commutations
                                            n_commutations[real_equip_analisado[j]] = altera_commutations
                                            max_comutacoes = max(n_commutations)
                                    print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))
                                    print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                                    print("Número de comutações internas: {}".format(intern_commutations))
                            
                                else:
                                    if equip_select < 2:
                                        for j in range(len(equip_analisado)):
                                            intern_commutations = 0
                                            if equip_analisado in list_cap_analisado: # não esquecer de alterar no outro também
                                                daily_commutations = list_cap_analisado.count(equip_analisado)                       
                                            else:
                                                daily_commutations = 1
                                            altera_commutations = intern_commutations + daily_commutations
                                            n_commutations[equip_analisado[j]] = altera_commutations
                                            max_comutacoes = max(n_commutations)
                                    else:
                                        for j in range(len(equip_analisado)):
                                            intern_commutations = 0
                                            if equip_analisado in list_equip_analisado: # não esquecer de alterar no outro também
                                                daily_commutations = list_equip_analisado.count(equip_analisado)                       
                                            else:
                                                daily_commutations = 1
                                            altera_commutations = intern_commutations + daily_commutations
                                            n_commutations[equip_analisado[j]] = altera_commutations
                                            max_comutacoes = max(n_commutations)
                                    print("\nNúmero de comutações diárias: {}".format(daily_commutations))
                                    print("Número de comutações internas: {}".format(intern_commutations))
                            print("\nAnálise das posições dos taps dos transformadores: {}".format(dict_trafos))





# -*- coding: utf-8 -*-
"""
@author: Patrick Alves
"""
from util.tabelas import LerTabelas
import pandas as pd

def calc_estoques(estoques, concessoes, probabilidades, populacao, segurados, periodo):
    
    calc_estoq_apos(estoques, concessoes, probabilidades, segurados, periodo)
    #calc_estoq_aux(estoques, probabilidades, segurados, periodo)
    #calc_estoq_salMat(estoques, populacao , segurados, periodo)

    return estoques

def calc_estoq_apos(est, conc, prob, seg, periodo):
    
    # Identificações das aposentadorias 
    ids_apos= ['Apin', 'Atcn', 'Apid', 'Atcp', 'Ainv', 'Atce', 'Atcd']

    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()

    # Obtem as aposentadorias para todas as clientelas e sexos
    lista_benef = dados.get_id_beneficios(ids_apos)
        
    for benef in lista_benef:
        # Verifica se o beneficio existe no Estoque
        if benef in est:
        
            sexo = benef[-1]                # Obtém o Sexo
            id_prob_morte = 'Mort'+ sexo    # ex: MortH
            id_fam = 'fam'+benef            # fator de ajuste de mortalidade            
            id_segurado = dados.get_id_segurados(benef)  # ex: CsmUrbH
            
            for ano in periodo:                
                # Adiciona uma nova coluna (ano) no DataFrame com valores zero
                est[benef][ano] = 0
                
                # 1 a 90 anos - Equação 11 da LDO de 2018
                for idade in range(1,91): 
                    est_ano_anterior = est[benef][ano-1][idade-1]
                    prob_sobreviver = 1 - prob[id_prob_morte][ano][idade] * prob[id_fam][idade]
                    entradas = seg[id_segurado][ano][idade] * prob[benef][idade]
                    est[benef].loc[idade, ano] = est_ano_anterior * prob_sobreviver + entradas     # Eq. 11
                    
                    # Salva a quantidade de concessões para uso posterior
                    conc[benef].loc[idade,ano] = entradas
                
                # Calculo para a idade zero
                est[benef].loc[0, ano] = seg[id_segurado][ano][0] * prob[benef][0]
                # Salva a quantidade de concessões para uso posterior
                conc[benef].loc[0, ano] = est[benef].loc[0, ano]
                
                # Ajuste para a idade de 90+ anos (modelo UFPA) - REVISAR
                #est[benef].loc[90, ano] = est[benef].loc[90, ano] + est[benef].loc[90, ano - 1]
                

    return est

# Projeta estoques para Auxílios Doença, Reclusão e Acidente - Equação 17 da LDO de 2018
def calc_estoq_aux(est, prob, seg, periodo):

    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()

    for benef in dados.get_id_beneficios(['Auxd', 'Auxa']):#'Auxr']): # REVISAR
        # Verifica se existe no Estoque
        if benef in est:            
            id_seg = dados.get_id_segurados(benef)
            
            for ano in periodo:
                # REVISAR: a Equação original usa a Pop, mas o certo seria os Segurados
                est[benef][ano] = seg[id_seg][ano] * prob[benef]     # Eq. 17
    
    return est
                
            
# Projeta estoques para Salário-Maternidade - Equação 20 da LDO de 2018 - REVISAR
def calc_estoq_salMat(est, pop, seg, periodo):

    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()

    for benef in dados.get_id_beneficios('SalMat'):            
        if benef in est:
            # Armazena valores do ano 
            est_acumulado = pd.Series(index=est[benef].columns)
                      
            id_seg = dados.get_id_segurados(benef)
            
            # Acumula mulheres de 16 a 45 anos para o estoque existente
            for ano in est[benef]:    
                est_acumulado[ano] = est[benef][ano].sum()
                    
            # Realiza projeção    
            for ano in periodo:
                est_acumulado[ano] = 0     # Cria um novo ano com valores zeros
                nascimentos = pop['PopIbgeM'][ano][0] + pop['PopIbgeH'][ano][0]
                
                # Acumula mulheres de 16 a 45 anos
                seg_16_45 = 0
                pop_16_45 = 0                                
                for idade in range(16,46):
                    seg_16_45 += seg[id_seg][ano][idade]
                    pop_16_45 += pop['PopIbgeM'][ano][idade]
                  
                est_acumulado[ano] = (seg_16_45/pop_16_45) * nascimentos    # Eq. 20
                
            est[benef] = est_acumulado
            
    return est
    

# Projeta os estoque de pensões - Equações 21 a 27 da LDO de 2018
def calc_estoq_pensoes(est, concessoes, prob, segurados, periodo):
    
    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()
    # Obtém o conjunto de benefícios do tipo pensão
    lista_pensoes = dados.get_id_beneficios('Pen')
    
    # Calcula pensões do tipo A
    for benef in lista_pensoes:    
        for ano in periodo:
            
            # Adiciona uma nova coluna (ano) no DataFrame com valores zero
            est[benef][ano] = 0
            
            sexo = benef[-1]                # Obtém o Sexo
            id_prob_morte = 'Mort'+ sexo    # ex: MortH
            id_fam = 'fam'+benef            # fator de ajuste de mortalidade
            id_pens = benef+"_tipoA"         # Cria um Id para pensão do tipo A
            
            # Copia os dados de estoque para Pensão do tipo A 
            est[id_pens] = est[benef].copy()
            
            # Projeta pensões do tipo A
            # Como não se tem novas concessões desse tipo de pensão, calcula-se
            # nas idades de 1 a 90 anos.
            for idade in range(1,91):
                est_ano_anterior = est[id_pens][ano-1][idade-1]
                prob_sobreviver = 1 - prob[id_prob_morte][ano][idade] * prob[id_fam][idade]
                                
                # Eq. 22
                est[id_pens].loc[idade, ano] = est_ano_anterior * prob_sobreviver

    
    # Calcula pensões de tipo B - Equação 23
    for benef in lista_pensoes:  
        
        sexo = benef[-1]                                                         # Obtém o Sexo
        sexo_oposto = 'M' if sexo=='H' else 'H'                                  # Obtém o oposto
        id_prob_morte = 'Mort'+ sexo                                             # ex: MortH
        id_mort_sex_op = 'Mort'+ sexo_oposto                                     # ex: MortM
        id_fam = 'fam'+benef                                                     # fator de ajuste de mortalidade
        id_pens = benef+"_tipoB"                                                 # Cria um Id para pensão do tipo A
        id_seg = dados.get_id_segurados(benef).replace(sexo, sexo_oposto)        # Obtem o Id do segurado trocando o sexo
        id_est_ac = dados.get_clientela(benef) + sexo_oposto                     # Obtem o Id do segurado trocando o sexo
            
        # Cria DataFrame para armazenar o estoque de Pensões do tipo B 
        est[id_pens] = pd.DataFrame(0.0, index=range(0,91), columns=[2014]+periodo)
        est[id_pens].index.name = "IDADE"        
              
        estoq_acum = calc_estoq_acumulado(est, periodo)
        
        for ano in periodo:           
            # Tipo de Pensão válida a partir de 2015            
            if ano < 2015:
                continue    # Pula anos inferiores a 2015
                     
            concessoes[benef][ano] = 0
            
            # Projeta pensões do tipo B            
            # Idades de 1 a 90 anos.
            for idade in range(1,91):
                dif = 0
                probab = 1 # temporareo
                est_ano_anterior = est[id_pens][ano-1][idade-1]
                prob_sobreviver = 1 - prob[id_prob_morte][ano][idade] * prob[id_fam][idade]
                conc = probab * (segurados[id_seg][ano][idade-dif] + estoq_acum[id_est_ac][ano][idade-dif]) * prob[id_mort_sex_op][ano][idade-dif]
                cessacoes = 0
                                
                # Eq. 23
                est[id_pens].loc[idade, ano] = est_ano_anterior * prob_sobreviver + conc - cessacoes
                
                # Salva o histórico de concessões
                concessoes[benef].loc[idade, ano] = conc
        
   # Pe = PeA + PeB      # Eq. 21
    
    return None


# Calcula as concessões de Pensões - REVISAR - FALTAM AS PROBABILIDADES DE PENSAO
# Equaçóes 24 e 25
def calc_concessoes_pensao(concessoes, estoques, segurados, prob, periodo):

    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()
    # Obtém o conjunto de benefícios do tipo pensão
    lista_pensoes = dados.get_id_beneficios('Pen')

    # Calcula pensões de tipo B - Equação 23
    for benef in lista_pensoes:  
        
        sexo = benef[-1]                                                         # Obtém o Sexo
        sexo_oposto = 'M' if sexo=='H' else 'H'                                  # Obtém o oposto
        id_mort_sex_op = 'Mort'+ sexo_oposto                                     # ex: MortM                
        id_seg = dados.get_id_segurados(benef).replace(sexo, sexo_oposto)        # Obtem o Id do segurado trocando o sexo
                
        # Obtém estoque acumulado de aposentadorias por clientela e sexo
        estoq_acum = calc_estoq_acumulado(estoques, periodo)
        
        for ano in periodo:           
            # Tipo de Pensão válida a partir de 2015            
            if ano < 2015:
                continue    # Pula anos inferiores a 2015
            
            # Cria nova entrada no DataFrame
            concessoes[benef][ano] = 0
            
            # Calcula concessões
            # Idades de 1 a 90 anos.
            for idade in range(1,91):
                dif = 0
                seg = segurados[id_seg][ano][idade-dif]
                est_ac = estoq_acum[id_seg][idade-dif]
                pmort = prob[id_mort_sex_op][idade-dif]
                
                # Eq. 24 e 25
                concessoes[benef][ano][idade] = prob * (seg + est_ac) * pmort
                
    return concessoes

# Calcula as cessações baseada no mecanismo legal de
# cessação automática da Lei nº 13.135/2015 - Equação 27 - REVISAR FALTAM AS CONCESSOES
def calc_cessacoes_pensao(cessacoes, concessoes, prob_mort, fam, periodo):
    
    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()

    # Parte da Eq. 27
    def get_ji(idade):
        
        if idade <= 23:
            return 3
        elif idade >=27 and idade <=32:
            return 6
        elif idade >=37 and idade <=39:
            return 10
        elif idade >=45 and idade <=55:
            return 15
        elif idade >=61 and idade <=63:
            return 20
        else:
            return 0

    # Calcula a probabilidade para cada tipo de pensão
    for beneficio in dados.get_id_beneficios(['Pens']):
        
        sexo = beneficio[-1]    # Obtém o sexo a partir do nome do benefício
        
        # Verifica se existe dados de estoque
        if beneficio in concessoes.keys():
            for ano in periodo:
                
                # Essa regra só vale a partir de 2015
                if ano < 2015:
                    continue    # Pula iteração
                
                # Cria nova entrada no Dataframe
                cessacoes[beneficio][ano] = 0
                                
                for idade in range(0,91):
                    ji = get_ji(idade)
                    conc = concessoes[beneficio][ano-ji][idade-ji]
                     
                    produtorio = 1
                    k = idade-ji
                    for i in range(k,idade):                        
                        pmorte = prob_mort['Mort'+sexo][ano-(i-k)][k]
                        fator = fam['fam'+beneficio][ano-(i-k)][k]
                        produtorio *= 1 - pmorte * fator
                        
                    cessacoes[beneficio][ano][idade] = conc * produtorio
                    


# Calcula estoque acumulado de aposentadorias por clientela e sexo
def calc_estoq_acumulado(estoques, periodo):
    
    # Cria o objeto dados que possui os IDs das tabelas
    dados = LerTabelas()
    
    ids_apos= ['Apin', 'Atcn', 'Apid', 'Atcp', 'Ainv', 'Atce', 'Atcd']

    # Dicionário que armazena o Estoque acumulado
    est_acumulado = {}
    
    # As chaves do dicionário são as clientelas
    for clientela in ['UrbPiso', 'UrbAcim', 'Rur']:                
        # Cria o DataFrame
        est_acumulado[clientela+'H'] = pd.DataFrame(0.0, index=range(0,91), columns=periodo)        
        est_acumulado[clientela+'M'] = pd.DataFrame(0.0, index=range(0,91), columns=periodo)        
        
        # Obtém todas as aposentadorias e faz o somatório por clientela
        for beneficio in dados.get_id_beneficios(ids_apos):                   
            # Verifica se o estoque para o benefício existe
            if beneficio in estoques.keys():
                sexo = beneficio[-1]
                if dados.get_clientela(beneficio) == clientela:                    
                    est_acumulado[clientela+sexo] += estoques[beneficio]
                                    
    return est_acumulado
                
                    

def calc_estoq_assistenciais(estoques, concessoes, populacao, prob, periodo):
    
    ids_assistenciais= ['LoasDef', 'LoasIdo', 'Rmv']

    for tipo in ids_assistenciais:
        for sexo in ['H', 'M']:            
            beneficio = tipo+sexo
            id_mort = 'Mort'+sexo
            id_fam = 'fam'+beneficio
            id_pop = "PopIbge"+sexo
            
            # Verifica se existe estoque para o benefício
            if beneficio in estoques.keys():
                for ano in periodo:                
                    # Cria uma nova entrada no DataFrame
                    estoques[beneficio][ano] = 0
                    
                    # Idades de 1 a 89 anos 
                    for idade in range(1,90):
                        est_ano_ant = estoques[beneficio][ano-1][idade-1]
                        prob_sobrev = 1 - prob[id_mort][ano][idade] * prob[id_fam][idade]
                        
                        # O RMV está em extinção (sem novas concessões)                    
                        if tipo == 'Rmv':
                            conc = 0
                        else:
                            conc = prob[beneficio][idade] * populacao[id_pop][ano][idade]
                            # Guarda histórico de concessões
                            concessoes[beneficio].loc[idade, ano] = conc
                       
                        # Eq.28 
                        est = (est_ano_ant * prob_sobrev) + conc
                        # Salva no DataFrame
                        estoques[beneficio].loc[idade, ano] = est                        
                        
                    # Idade zero e 90 - REVISAR                    
                    est_90_ant = estoques[beneficio][ano-1][90]
                    # O RMV está em extinção (sem novas concessões)                    
                    if tipo == 'Rmv':
                        conc = 0
                    else:
                        # Idade zero - REVISAR - o valor esta aumentando muito
                        estoques[beneficio].loc[0, ano] = prob[beneficio][0] * populacao[id_pop][ano][0]
                        concessoes[beneficio].loc[0, ano] = estoques[beneficio].loc[0, ano]
                        # Idade 90 - REVISAR - Tendência de queda constante
                        conc = prob[beneficio][90] * (populacao[id_pop][ano][90] - est_90_ant)                  
                        concessoes[beneficio].loc[90, ano] = conc
                                            
                    prob_sobrev = 1 - prob[id_mort][ano][90] * prob[id_fam][90]
                    estoques[beneficio].loc[90, ano] = (est_90_ant * prob_sobrev) + conc
                    
    return estoques
                    
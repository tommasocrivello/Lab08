from database.distributore_DAO import DistributoreDAO

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        # TODO
        risultato = []
        for distributore in self._distributori:
            tutti_i_prezzi = distributore.get_prezzi()
            # L'attributo .data è un oggetto datetime, quindi possiamo estrarre il mese con .month
            prezzi_mese = [p.prezzo_litro for p in tutti_i_prezzi if p.data.month == mese]
            if len(prezzi_mese) > 0:
                media = sum(prezzi_mese) / len(prezzi_mese)
                risultato.append((distributore.nome, media))
            else:
                risultato.append((distributore.nome, 0.0))
        return risultato

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        # TODO
        # 🚨 1. CASO BASE (Condizione di Terminazione)
        # Se siamo arrivati a completare 7 giorni (il "giorno" è diventato 8)
        if giorno > 7:
            # Mi chiedo: è la prima volta che arrivo in fondo (-1)
            # OPPURE ho trovato un costo minore del mio record attuale?
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                # FONDAMENTALE IL .copy()! Come nelle N-Regine, altrimenti ai giri
                # successivi la lista verrebbe svuotata dal backtracking
                self.__sequenza_ottima = sequenza_parziale.copy()
            return  # Esco dal ramo

        # 🚨 2. PRUNING (Ottimizzazione - "Branch and Bound")
        # Se il mio costo_corrente ha GIÀ superato il costo ottimo (il record),
        # è matematicamente inutile andare avanti a calcolare i giorni successivi.
        # Taglio il ramo e torno indietro subito!
        if self.__costo_ottimo != -1 and costo_corrente >= self.__costo_ottimo:
            return

        # 3. ESPLORAZIONE
        # Al bivio ho due scelte: andare dal Distributore A o dal Distributore B
        for distributore in self._distributori:
            id_distributore = distributore.id

            # -- CALCOLO I COSTI DELLA SCELTA --
            # Attenzione agli indici: per il "giorno 1" devo pescare all'indice 0
            prezzo_litro_oggi = prezzi_settimana[id_distributore][giorno - 1]
            costo_carburante = prezzo_litro_oggi * 100

            costo_spostamento = 0
            # Aggiungo la penale di 5€ SOLO SE:
            # 1. Non sono al primo giorno (ultimo_distributore non è None)
            # 2. Ho cambiato distributore rispetto a ieri
            if ultimo_distributore is not None and ultimo_distributore != id_distributore:
                costo_spostamento = 5

            costo_giornata_totale = costo_carburante + costo_spostamento

            # 🚨 4. SPORCO LO STATO (Aggiungo la mia scelta)
            sequenza_parziale.append(id_distributore)

            # 🚨 5. RICORSIONE IN PROFONDITÀ
            # Passo al giorno successivo (giorno + 1), aggiorno il costo, e dichiaro la mia scelta di oggi
            self.__ricorsione(sequenza_parziale, giorno + 1, id_distributore, costo_corrente + costo_giornata_totale,
                              prezzi_settimana)

            # 🚨 6. BACKTRACKING (La gomma da cancellare)
            # Sono tornato su. Cancello l'ultimo distributore aggiunto per poter
            # provare il prossimo nel ciclo for.
            sequenza_parziale.pop()

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        # TODO
        prezzi_settimana = {}

        for distributore in self._distributori:
            # 1. Recupero tutti i prezzi tramite l'ORM (stessa cosa del Punto 1)
            tutti_i_prezzi = distributore.get_prezzi()

            # 2. Filtro per il mese esatto E per i primi 7 giorni
            prezzi_filtrati = [p for p in tutti_i_prezzi if p.data.month == mese and p.data.day <= 7]

            # 3. Sicurezza extra: ordino la lista per giorno, così sono certo
            # che l'indice 0 sia il giorno 1, l'indice 1 sia il giorno 2, ecc.
            prezzi_filtrati.sort(key=lambda x: x.data.day)

            # 4. Estraggo solo il numerino del prezzo (float) e lo metto nel dizionario
            prezzi_settimana[distributore.id] = [p.prezzo_litro for p in prezzi_filtrati]

        return prezzi_settimana
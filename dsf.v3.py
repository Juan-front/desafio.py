import textwrap
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime
from pathlib import Path

ROOT_PATH = Path(__file__).parent

class Cliente:
    def __init__(self, nome, cpf, endereco):
        self.nome = nome
        self.cpf = cpf
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)

class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(nome, cpf, endereco)
        self.data_nascimento = data_nascimento


class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente
    
    @property 
    def historico(self):
        return self._historico

    def sacar(self, valor):
        if valor > self._saldo:
            print("\nOperação falhou! Você não tem saldo suficiente.")
        elif valor > 0:
            self._saldo -= valor
            print(f"\nSaque de R$ {valor:.2f} realizado com sucesso!")
            return True
        else:
            print("\nOperação falhou! O valor informado é inválido.")
            return False

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print(f"\nDepósito de R$ {valor:.2f} realizado com sucesso!")
        else:
            print("\nOperação falhou! O valor informado é inválido.")
            return False
        return True
    
    def realizar_transacao(self, transacao):
        transacao.registrar(self)


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=800, limite_saques=3):
        super().__init__(numero, cliente) 
        self.limite = limite
        self.limite_saques = limite_saques

    def sacar(self, valor):
        numero_saques = len(
            [transacao for transacao in self.historico.transacoes if transacao["tipo"] == "Saque"]
        ) 

        excedeu_limite = valor > self.limite
        excedeu_saques = numero_saques >= self.limite_saques

        if excedeu_limite:
            print("\nValor de saque excedido!")
        elif excedeu_saques:
            print("\nNúmero de saques excedidos!")
        else:
            return super().sacar(valor)
        
        return False  

    def __str__(self):
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
        """

class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower() == tipo_transacao.lower():
                yield transacao

    def transacoes_do_dia(self):
        data_atual = datetime.utcnow().date()
        transacoes = []
        for transacao in self._transacoes:
            data_transacao = datetime.strptime(transacao["data"], "%d-%m-%Y %H:%M:%S").date()
            if data_atual == data_transacao:
                transacoes.append(transacao)
        return transacoes

class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass

class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)

class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self) 

def log_transacao(func):
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        data_hora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with open(ROOT_PATH / "log.txt", "a") as arquivo:
            arquivo.write(
                f"[{data_hora}] Função '{func.__name__}' executada com argumentos {args} e {kwargs}. "
                f"Retornou {resultado}\n"
            )
        return resultado
    return envelope

def menu():
    menu = """\n
    ================ MENU ================
    [1]\tDepositar
    [2]\tSacar
    [3]\tExtrato
    [4]\tNovo usuario
    [5]\tCriar conta
    [0]\tSair
    => """
    return input(textwrap.dedent(menu))

def filtrar_usuario(cpf, usuarios):
    """Função que filtra um usuário pelo CPF."""
    return next((usuario for usuario in usuarios if usuario.cpf == cpf), None)

def depositar(contas):
    numero_conta = input("Informe o número da conta: ")
    valor = float(input("Informe o valor do depósito: R$ "))
    
    # Procurar a conta
    conta = next((conta for conta in contas if conta["numero_conta"] == numero_conta), None)
    
    if conta:
        # Chama o método depositar diretamente da conta
        deposito = Deposito(valor)
        conta["conta"].realizar_transacao(deposito)  # Registrar a transação diretamente
    else:
        print("\nConta não encontrada!")

def sacar(contas):
    numero_conta = input("Informe o número da conta: ")
    valor = float(input("Informe o valor do saque: R$ "))
    
    # Procurar a conta
    conta = next((conta for conta in contas if conta["numero_conta"] == numero_conta), None)
    if conta:
        # Criar a transação de saque
        saque = Saque(valor)
        conta["conta"].realizar_transacao(saque)  # Registrar a transação diretamente
    else:
        print("\nConta não encontrada!")

def criar_usuario(usuarios):
    """Função para criar um novo usuário"""
    nome = input("Informe o nome do usuário: ")
    cpf = input("Informe o CPF do usuário: ")
    endereco = input("Informe o endereço do usuário: ")
    usuario = PessoaFisica(nome, "", cpf, endereco)
    usuarios.append(usuario)
    print("\nUsuário criado com sucesso!")

def criar_conta(usuarios, contas):
    cpf = input("Informe o CPF do usuário: ")
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        numero_conta = input("Informe o número da conta (ou deixe em branco para gerar automaticamente): ")
        if not numero_conta:
            numero_conta = f"{cpf[-4:]}{len(contas) + 1}"  # Gerar um número único de conta

        conta = ContaCorrente(numero_conta, usuario)
        contas.append({"numero_conta": numero_conta, "conta": conta, "usuario": usuario})
        usuario.adicionar_conta(conta)
        print("\n=== Conta criada com sucesso! ===")
    else:
        print("\nUsuário não encontrado, fluxo de criação de conta encerrado!")

def exibir_extrato(conta):
    print("\n================ EXTRATO ================")
    if not conta.historico.transacoes:
        print("Não foram realizadas movimentações.")
    else:
        for transacao in conta.historico.transacoes:
            print(f"{transacao['tipo']} de R$ {transacao['valor']:.2f} em {transacao['data']}")
            print(f"Saldo atual: R$ {conta.saldo:.2f}")
            print("==========================================")

def main():
    usuarios = []
    contas = []
    
    while True:
        opcao = menu()

        if opcao == "1":
            # Realizar depósito
            depositar(contas)

        elif opcao == "2":
            # Realizar saque
            sacar(contas)

        elif opcao == "3":
            # Exibir extrato
            numero_conta = input("Informe o número da conta para extrato: ")
            conta = next((c for c in contas if c["numero_conta"] == numero_conta), None)
            if conta:
                exibir_extrato(conta["conta"])
            else:
                print("Conta não encontrada!")

        elif opcao == "4":
            # Criar usuário
            criar_usuario(usuarios)

        elif opcao == "5":
            # Criar conta
            criar_conta(usuarios, contas)

        elif opcao == "0":
            print("Volte sempre!")
            break

main()

from django.db import models


class ConfiguracaoJogo(models.Model):
    """
    Armazena as configurações globais e preferências que são carregadas
    assim que o jogador abre o menu inicial do Cuphead Web.
    """
    identificador = models.CharField(max_length=50, default="padrao", unique=True)
    ultimo_apelido = models.CharField(max_length=30, default="Cuphead")
    som_mutado = models.BooleanField(default=False)
    # Permite ajustar parâmetros iniciais do jogo direto pelo banco se desejar
    hp_inicial_jogador = models.IntegerField(default=3)
    hp_maximo_chefe = models.IntegerField(default=550)
    velocidade_jogador = models.FloatField(default=340.0)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuração ({self.identificador}) - Mudo: {self.som_mutado}"


class ProgressoSalvo(models.Model):
    """
    Sistema de Save (Progresso): Mapeia exatamente as variáveis de estado
    da partida em andamento no JavaScript para permitir Salvar e Carregar (Continue).
    """
    nome_jogador = models.CharField(max_length=30, unique=True, default="Cuphead")
    pontuacao = models.IntegerField(default=0)
    tempo_jogo = models.FloatField(default=0.0)

    # Estado do Jogador (objeto `jogador` no JS)
    jogador_hp = models.IntegerField(default=3)
    jogador_medidor_especial = models.FloatField(default=0.0)  # 0 a 500 (5 cartas)
    jogador_x = models.FloatField(default=140.0)
    jogador_y = models.FloatField(default=401.0)

    # Estado do Chefe (objeto `chefe` no JS - Barão Von Mostarda)
    chefe_hp = models.FloatField(default=550.0)
    chefe_fase = models.IntegerField(default=1)  # Fases 1, 2 ou 3

    salvo_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Save de {self.nome_jogador} | Fase {self.chefe_fase}/3 | HP: {self.jogador_hp}"


class PlacarLeaderboard(models.Model):
    """
    Leaderboard (Placar Top 10): Registra o resultado final quando o jogador
    vence (KNOCKOUT!) ou perde todas as 3 vidas (YOU DIED!).
    """
    nome_jogador = models.CharField(max_length=30)
    pontuacao = models.IntegerField()
    vitoria = models.BooleanField(default=False)
    fase_alcancada = models.IntegerField(default=1)
    tempo_jogo = models.FloatField(default=0.0)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ordena automaticamente da maior pontuação para a menor (e menor tempo como desempate)
        ordering = ['-pontuacao', 'tempo_jogo']

    def __str__(self):
        status = "KNOCKOUT" if self.vitoria else "GAME OVER"
        return f"{self.nome_jogador} - {self.pontuacao} pts ({status})"
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ConfiguracaoJogo, ProgressoSalvo, PlacarLeaderboard


def adicionar_cabecalhos_cors(response):
    """
    Auxiliar para permitir que o HTML rode mesmo se aberto em outra porta
    (ex: Live Server na porta 5500 consumindo o Django na porta 8000).
    """
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def tela_jogo(request):
    """Renderiza o arquivo index.html principal caso acesse pela raiz do Django."""
    return render(request, 'index.html')


# ==============================================================================
# 1. ROTA DE CONFIGURAÇÕES (Carregada ao abrir o menu inicial e salva ao mutar som)
# ==============================================================================
@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def api_configuracoes(request):
    if request.method == "OPTIONS":
        return adicionar_cabecalhos_cors(JsonResponse({"status": "ok"}))

    config, _ = ConfiguracaoJogo.objects.get_or_create(identificador="padrao")

    if request.method == "GET":
        # Verifica também se já existe um save ativo para esse jogador habilitar o botão "Continuar"
        tem_save = ProgressoSalvo.objects.filter(nome_jogador=config.ultimo_apelido).exists()
        dados = {
            "sucesso": True,
            "ultimo_apelido": config.ultimo_apelido,
            "som_mutado": config.som_mutado,
            "hp_inicial_jogador": config.hp_inicial_jogador,
            "hp_maximo_chefe": config.hp_maximo_chefe,
            "velocidade_jogador": config.velocidade_jogador,
            "possui_save": tem_save,
        }
        return adicionar_cabecalhos_cors(JsonResponse(dados))

    elif request.method == "POST":
        try:
            corpo = json.loads(request.body)
            if "som_mutado" in corpo:
                config.som_mutado = bool(corpo["som_mutado"])
            if "ultimo_apelido" in corpo and str(corpo["ultimo_apelido"]).strip():
                config.ultimo_apelido = str(corpo["ultimo_apelido"]).strip()[:30]
            config.save()
            return adicionar_cabecalhos_cors(JsonResponse({
                "sucesso": True,
                "som_mutado": config.som_mutado,
                "ultimo_apelido": config.ultimo_apelido
            }))
        except Exception as erro:
            return adicionar_cabecalhos_cors(JsonResponse({"sucesso": False, "erro": str(erro)}, status=400))


# ==============================================================================
# 2. ROTA DE SAVE / PROGRESSO (Salvar na Pausa/Transição de Fase e Carregar)
# ==============================================================================
@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def api_progresso(request):
    if request.method == "OPTIONS":
        return adicionar_cabecalhos_cors(JsonResponse({"status": "ok"}))

    if request.method == "GET":
        nome = request.GET.get("nome_jogador", "Cuphead").strip() or "Cuphead"
        try:
            save = ProgressoSalvo.objects.get(nome_jogador=nome)
            return adicionar_cabecalhos_cors(JsonResponse({
                "sucesso": True,
                "tem_save": True,
                "progresso": {
                    "nome_jogador": save.nome_jogador,
                    "pontuacao": save.pontuacao,
                    "tempo_jogo": save.tempo_jogo,
                    "jogador_hp": save.jogador_hp,
                    "jogador_medidor_especial": save.jogador_medidor_especial,
                    "jogador_x": save.jogador_x,
                    "jogador_y": save.jogador_y,
                    "chefe_hp": save.chefe_hp,
                    "chefe_fase": save.chefe_fase,
                    "salvo_em": save.salvo_em.strftime("%d/%m/%Y %H:%M")
                }
            }))
        except ProgressoSalvo.DoesNotExist:
            return adicionar_cabecalhos_cors(JsonResponse({"sucesso": True, "tem_save": False}))

    elif request.method == "POST":
        try:
            corpo = json.loads(request.body)
            nome = str(corpo.get("nome_jogador", "Cuphead")).strip()[:30] or "Cuphead"

            # Se a flag `limpar_save` vier como True (ex: quando termina a partida), apaga o save
            if corpo.get("limpar_save"):
                ProgressoSalvo.objects.filter(nome_jogador=nome).delete()
                return adicionar_cabecalhos_cors(JsonResponse({"sucesso": True, "mensagem": "Save removido após fim de jogo."}))

            save, _ = ProgressoSalvo.objects.update_or_create(
                nome_jogador=nome,
                defaults={
                    "pontuacao": int(corpo.get("pontuacao", 0)),
                    "tempo_jogo": float(corpo.get("tempo_jogo", 0.0)),
                    "jogador_hp": int(corpo.get("jogador_hp", 3)),
                    "jogador_medidor_especial": float(corpo.get("jogador_medidor_especial", 0.0)),
                    "jogador_x": float(corpo.get("jogador_x", 140.0)),
                    "jogador_y": float(corpo.get("jogador_y", 401.0)),
                    "chefe_hp": float(corpo.get("chefe_hp", 550.0)),
                    "chefe_fase": int(corpo.get("chefe_fase", 1)),
                }
            )
            return adicionar_cabecalhos_cors(JsonResponse({
                "sucesso": True,
                "mensagem": f"Progresso salvo na Fase {save.chefe_fase}/3!"
            }))
        except Exception as erro:
            return adicionar_cabecalhos_cors(JsonResponse({"sucesso": False, "erro": str(erro)}, status=400))


# ==============================================================================
# 3. ROTA DE LEADERBOARD (Salvar pontuação no Game Over/Vitória e Listar Top 10)
# ==============================================================================
@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def api_leaderboard(request):
    if request.method == "OPTIONS":
        return adicionar_cabecalhos_cors(JsonResponse({"status": "ok"}))

    if request.method == "POST":
        try:
            corpo = json.loads(request.body)
            nome = str(corpo.get("nome_jogador", "Cuphead")).strip()[:30] or "Cuphead"
            pontuacao = int(corpo.get("pontuacao", 0))
            vitoria = bool(corpo.get("vitoria", False))
            fase_alcancada = int(corpo.get("fase_alcancada", 1))
            tempo_jogo = float(corpo.get("tempo_jogo", 0.0))

            PlacarLeaderboard.objects.create(
                nome_jogador=nome,
                pontuacao=pontuacao,
                vitoria=vitoria,
                fase_alcancada=fase_alcancada,
                tempo_jogo=tempo_jogo
            )

            # Também atualiza o último apelido usado nas configurações
            ConfiguracaoJogo.objects.update_or_create(
                identificador="padrao",
                defaults={"ultimo_apelido": nome}
            )

            # Remove o save temporário pois a partida foi concluída
            ProgressoSalvo.objects.filter(nome_jogador=nome).delete()

        except Exception as erro:
            return adicionar_cabecalhos_cors(JsonResponse({"sucesso": False, "erro": str(erro)}, status=400))

    # Tanto no GET quanto após salvar no POST, retorna o Top 10 atualizado
    top_10_qs = PlacarLeaderboard.objects.all()[:10]
    top_10 = [
        {
            "posicao": idx + 1,
            "nome_jogador": item.nome_jogador,
            "pontuacao": item.pontuacao,
            "vitoria": item.vitoria,
            "fase_alcancada": item.fase_alcancada,
            "tempo_jogo": round(item.tempo_jogo, 1),
            "data": item.data_registro.strftime("%d/%m %H:%M")
        }
        for idx, item in enumerate(top_10_qs)
    ]

    return adicionar_cabecalhos_cors(JsonResponse({
        "sucesso": True,
        "top_10": top_10
    }))
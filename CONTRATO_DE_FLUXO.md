# 🧾 CONTRATO DE FLUXO — PADRÃO TREVIS

> **Versão:** 1.0  
> **Autor:** Trevis  
> **Propósito:** Garantir consistência, previsibilidade e qualidade técnica em cada iteração de código, build e infraestrutura.  
> **Princípio central:** Alteração mínima, justificada e reversível — *nunca degrade o que funciona.*

---

## 📘 SUMÁRIO
- [🎯 Objetivo](#-objetivo)
- [🧩 1. Princípios de Operação](#-1-princípios-de-operação)
- [⚙️ 2. Processo de Iteração](#️-2-processo-de-iteração)
- [🧠 3. Padrão de Qualidade](#-3-padrão-de-qualidade)
- [🧩 4. Comunicação Técnica](#-4-comunicação-técnica)
- [✅ 5. Acordo Final](#-5-acordo-final)

---

## 🎯 Objetivo

Assegurar **qualidade, rastreabilidade e coerência técnica** em todo o ciclo de desenvolvimento.  
Nenhum ajuste é feito sem clareza total de *o que muda*, *por que muda* e *qual o impacto direto*.

> 🧠 Este contrato rege interações com IA, revisões humanas e fluxos automatizados que alterem código, dependências ou infraestrutura.

---

## 🧩 1. Princípios de Operação

<details>
<summary><b>📄 Transparência total</b></summary>
Toda modificação deve apresentar o <ins>diff completo</ins> — antes/depois — para validação explícita.  
Nada é aplicado às cegas.
</details>

<details>
<summary><b>🔍 Justificativa técnica obrigatória</b></summary>
Cada alteração precisa descrever **o motivo técnico e o problema que resolve**.  
Sem “melhorias” vagas ou genéricas.
</details>

<details>
<summary><b>🧱 Alteração mínima viável (AMV)</b></summary>
Muda-se apenas o necessário.  
Sem refatorações cosméticas ou otimizações sem ganho real.
</details>

<details>
<summary><b>💬 Comentários preservados</b></summary>
Nenhum comentário, docstring, log ou diagnóstico é removido sem motivo técnico explícito.
</details>

<details>
<summary><b>♻️ Reversibilidade garantida</b></summary>
Toda mudança deve poder ser revertida com `git checkout -p`.  
Sem efeitos colaterais ocultos.
</details>

<details>
<summary><b>🚦 Validação incremental</b></summary>
Valida-se cada parte isoladamente (ex: `requirements.txt` antes de `Dockerfile`) para evitar cascatas de erro.
</details>

---

## ⚙️ 2. Processo de Iteração

1️⃣ **Análise contextual**
- Verificar versão atual e dependências.  
- Entender o impacto da alteração no build, runtime e deploy.

2️⃣ **Proposta com diff**
```diff
- antiga linha
+ nova linha
```

Sempre acompanhado de uma explicação:
“Corrige X para evitar Y”

3️⃣ Aprovação explícita
Nada é aplicado sem confirmação do Trevis
(“ok”, “pode aplicar”, “confirma”).

4️⃣ Commit padronizado
Usar Conventional Commits:
```yaml
fix: corrige erro de build no torch
feat: adiciona geração automática de VTT
refactor: reorganiza app.py mantendo comportamento

```

5️⃣ Verificação pós-merge
Após merge ou rebuild:

Revisar logs de execução;

Confirmar endpoints e GPU ativos;

Validar integridade do resultado.

🧠 3. Padrão de Qualidade

Código determinístico (sem latest, sem dependências implícitas).

Build reproduzível via Docker e requirements.txt fixos.

Logs e erros explícitos e acionáveis.

Lógica funcional nunca é substituída por estética.

Toda alteração precisa aumentar estabilidade, previsibilidade ou clareza.

🧩 4. Comunicação Técnica

Linguagem direta e técnica, sem floreio.

Cada resposta deve conter:

✅ O que muda

✅ Por que muda

✅ Efeito prático esperado

Em caso de dúvida ou ambiguidade: pausar e revisar antes de tocar no código.

Nenhum “ajuste automático” sem revisão do Trevis.

✅ 5. Acordo Final

“Nada entra em produção sem clareza total.
Alteração mínima, justificada e reversível.
Zero perda de qualidade.”

© Trevis — 2025
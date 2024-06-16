# Importando as bibliotecas necessárias
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict
import json, uuid

# Inicializando a aplicação FastAPI
app = FastAPI()

# Definindo o modelo de dados para uma Nota
class Nota(BaseModel):
    valor: float = Field(..., ge=0, le=10)  # A nota é um float entre 0 e 10

# Definindo o modelo de dados para um Aluno
class Alunos(BaseModel):
    nome: str  # O nome do aluno é uma string
    notas: Dict[str, Nota]  # As notas do aluno são um dicionário mapeando nomes de disciplinas para Notas

# Inicializando o banco de dados de alunos como um dicionário
students_db: Dict[str, Alunos] = {}

# Função para salvar o banco de dados de alunos em um arquivo JSON
def save_db():
    with open('students.json', 'w') as f:
        json.dump({k: v.model_dump() for k, v in students_db.items()}, f)


# Função para carregar o banco de dados de alunos de um arquivo JSON
def load_db():
    try:
        with open('students.json', 'r') as f:
            students_db.update({k: Alunos(**v) for k, v in json.load(f).items()})
    except FileNotFoundError:
        pass  # Se o arquivo não existir, não fazemos nada

# Rota para criar um novo aluno
@app.post("/students/{nome}")
async def create_student(nome: str, notas: Dict[str, Nota]):
    load_db()  # Carregando o banco de dados de alunos
    student_id = str(uuid.uuid4())  # Gerando um ID único para o aluno
    student = Alunos(nome=nome, notas=notas)  # Criando um novo objeto Alunos
    students_db[student_id] = student  # Adicionando o aluno ao banco de dados
    save_db()  # Salvando o banco de dados em um arquivo
    return {"id": student_id, "student": student}  # Retornando o ID e os dados do aluno

# Rota para obter todos os alunos registrados
@app.get("/students")
async def get_all_students():
    load_db()  # Carregando o banco de dados de alunos
    return {student_id: s.model_dump() for student_id, s in students_db.items()}  # Retornando todos os alunos registrados

# Rota para ler os dados de um aluno específico
@app.get("/students/{student_id}")
async def read_student(student_id: str):
    load_db()  # Carregando o banco de dados de alunos
    return students_db[student_id]  # Retornando os dados do aluno solicitado

# Rota para ler as notas de uma disciplina específica
@app.get("/subjects/{subject_name}")
async def read_subject(subject_name: str):
    load_db()  # Carregando o banco de dados de alunos
    subject_grades = [(s.nome, s.notas[subject_name].valor) for s in students_db.values() if subject_name in s.notas]  # Obtendo as notas da disciplina solicitada
    subject_grades.sort(key=lambda x: x[1])  # Ordenando as notas em ordem crescente
    return subject_grades  # Retornando as notas da disciplina

# endpoint para calcular estatísticas de desempenho de uma disciplina
@app.get("/subjects/{subject_name}/stats")
async def get_subject_stats(subject_name: str):
    load_db()  # Carregando o banco de dados de alunos
    grades = [s.notas[subject_name].valor for s in students_db.values() if subject_name in s.notas]  # Obtendo as notas da disciplina solicitada
    return {
        "media": sum(grades) / len(grades),  # Calculando a média das notas
        "mediana": sorted(grades)[len(grades) // 2] if len(grades) % 2 == 1 else sum(sorted(grades)[len(grades) // 2 - 1 : len(grades) // 2 + 1]) / 2,  # Calculando a mediana das notas
        "desvio_padrao": (sum((x - sum(grades) / len(grades)) ** 2 for x in grades) / len(grades)) ** 0.5  # Calculando o desvio padrão das notas
    }

# endpoint para identificar alunos com desempenho abaixo do esperado
@app.get("/alunos/low_performance")
async def get_low_performance_students():
    load_db()  # Carregando o banco de dados de alunos
    low_performance_students = [{"id": student_id, "nome": s.nome} for student_id, s in students_db.items() if any(nota.valor < 6.0 for nota in s.notas.values())]
    return {"Alunos com desempenho abaixo do esperado": low_performance_students}  # Retornando os alunos com desempenho abaixo do esperado

# endpoint para remover alunos que têm 0 em todas as disciplinas
@app.delete("/students/no_grades")
async def delete_students_with_no_grades():
    load_db()  # Carregando o banco de dados de alunos
    students_with_no_grades = {student_id: s for student_id, s in students_db.items() if all(nota.valor == 0 for nota in s.notas.values())}
    students_with_grades = {student_id: s for student_id, s in students_db.items() if not all(nota.valor == 0 for nota in s.notas.values())}
    students_db.clear()  # Limpando o banco de dados de alunos
    students_db.update(students_with_grades)  # Atualizando o banco de dados com os alunos que têm notas
    save_db()  # Salvando o banco de dados em um arquivo
    return {"message": "Alunos sem notas foram removidos", "Alunos removidos": [{"id": student_id, "nome": s.nome} for student_id, s in students_with_no_grades.items()]}  # Retornando uma mensagem indicando que os alunos sem notas foram removidos e a lista de alunos removidos

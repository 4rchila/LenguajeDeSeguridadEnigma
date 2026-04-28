"""
codegen/policy_exporter.py — Generador de Políticas JSON (Fase 4)
=================================================================
Recorre el AST validado semánticamente y la Tabla de Símbolos para
producir un documento JSON estructurado con todas las políticas de
acceso compiladas.

Este archivo JSON puede ser consumido por sistemas externos (ERPs,
aplicaciones web, APIs REST, middleware de autorización) para aplicar
las reglas RBAC/ABAC definidas en el lenguaje Enigma.

Estructura de salida:
    {
      "enigma_version": "1.0",
      "metadata": { ... },
      "entities": { roles, users, modules },
      "policies": { role_policies, user_assignments },
      "abac_rules": [ ... ],
      "access_matrix": { role → { module → [actions] } }
    }
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import parser.ast_nodes as ast
from semantic.symbol_table import (
    SymbolTable,
    Symbol,
    TIPO_ROL,
    TIPO_USUARIO,
    TIPO_MODULO,
    TIPO_VARIABLE_ENTORNO,
)


class PolicyExporter:
    """
    Traversa el AST y la Tabla de Símbolos para generar un JSON
    de políticas compiladas listo para integración externa.
    """

    def __init__(self, arbol: ast.ProgramNode, tabla: SymbolTable,
                 source_file: str = ""):
        self.arbol = arbol
        self.tabla = tabla
        self.source_file = source_file

    def exportar(self) -> Dict[str, Any]:
        """Genera el diccionario completo de políticas compiladas."""
        return {
            "enigma_version": "1.0",
            "metadata": self._build_metadata(),
            "environment_variables": self._build_env_vars(),
            "entities": self._build_entities(),
            "policies": self._build_policies(),
            "abac_rules": self._build_abac_rules(),
            "access_matrix": self._build_access_matrix(),
        }

    def exportar_json(self, indent: int = 2) -> str:
        """Retorna el JSON como string formateado."""
        return json.dumps(self.exportar(), indent=indent, ensure_ascii=False)

    # ─────────────────────────────────────────────────────────────
    # Secciones del documento
    # ─────────────────────────────────────────────────────────────

    def _build_metadata(self) -> Dict[str, Any]:
        return {
            "compiled_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": self.source_file or "stdin",
            "status": "valid",
            "total_roles": sum(1 for s in self.tabla if s.tipo_dato == TIPO_ROL),
            "total_users": sum(1 for s in self.tabla if s.tipo_dato == TIPO_USUARIO),
            "total_modules": sum(1 for s in self.tabla if s.tipo_dato == TIPO_MODULO),
        }

    def _build_env_vars(self) -> List[Dict[str, str]]:
        """Variables ABAC globales disponibles en el entorno."""
        return [
            {
                "name": s.identificador,
                "type": s.sub_tipo or "Unknown",
            }
            for s in self.tabla
            if s.tipo_dato == TIPO_VARIABLE_ENTORNO and s.es_global
        ]

    def _build_entities(self) -> Dict[str, Any]:
        roles = []
        users = []
        modules = []

        for s in self.tabla:
            if s.tipo_dato == TIPO_ROL:
                roles.append({
                    "id": s.identificador,
                    "declared_at": {"line": s.linea, "column": s.columna},
                })
            elif s.tipo_dato == TIPO_USUARIO:
                users.append({
                    "id": s.identificador,
                    "assigned_role": s.rol_vinculado,
                    "declared_at": {"line": s.linea, "column": s.columna},
                })
            elif s.tipo_dato == TIPO_MODULO:
                modules.append({
                    "id": s.identificador,
                    "declared_at": {"line": s.linea, "column": s.columna},
                })

        return {
            "roles": roles,
            "users": users,
            "modules": modules,
        }

    def _build_policies(self) -> Dict[str, Any]:
        """Políticas estáticas RBAC extraídas de la Tabla de Símbolos."""
        role_policies = []
        user_assignments = []

        for s in self.tabla:
            if s.tipo_dato == TIPO_ROL and s.politicas:
                for accion, operacion, modulo in s.politicas:
                    role_policies.append({
                        "role": s.identificador,
                        "action": accion,
                        "operation": operacion,
                        "module": modulo,
                        "effect": "allow" if accion.lower() in ("permitir", "acceder") else "deny",
                    })

            if s.tipo_dato == TIPO_USUARIO and s.rol_vinculado:
                user_assignments.append({
                    "user": s.identificador,
                    "role": s.rol_vinculado,
                })

        return {
            "role_policies": role_policies,
            "user_assignments": user_assignments,
        }

    def _build_abac_rules(self) -> List[Dict[str, Any]]:
        """Extrae reglas condicionales (Si/Mientras) del AST."""
        rules = []
        if self.arbol:
            self._extract_conditions(self.arbol, rules)
        return rules

    def _build_access_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Genera una matriz de acceso resumida:
        { "Gerente": { "Reportes": ["Permitir Consultar"], "Ventas": ["Denegar Eliminar"] } }
        """
        matrix = {}
        for s in self.tabla:
            if s.tipo_dato == TIPO_ROL and s.politicas:
                role_entry = {}
                for accion, operacion, modulo in s.politicas:
                    if modulo not in role_entry:
                        role_entry[modulo] = []
                    label = f"{accion} {operacion}" if operacion else accion
                    role_entry[modulo].append(label)
                matrix[s.identificador] = role_entry
        return matrix

    # ─────────────────────────────────────────────────────────────
    # Extracción recursiva de reglas ABAC del AST
    # ─────────────────────────────────────────────────────────────

    def _extract_conditions(self, node: ast.ASTNode, rules: list):
        """Recorre recursivamente el AST buscando nodos Si/Mientras."""
        if node is None:
            return

        if isinstance(node, ast.SiEntoncesNode):
            rule = {
                "type": "conditional",
                "keyword": "Si",
                "condition": self._serialize_condition(node.condicion),
                "then_actions": self._extract_actions(node.bloque_entonces),
            }
            if node.bloque_sino:
                rule["else_actions"] = self._extract_actions(node.bloque_sino)
            rules.append(rule)
            # Recurse into branches for nested conditions
            self._extract_conditions(node.bloque_entonces, rules)
            if node.bloque_sino:
                self._extract_conditions(node.bloque_sino, rules)

        elif isinstance(node, ast.MientrasNode):
            rules.append({
                "type": "loop",
                "keyword": "Mientras",
                "condition": self._serialize_condition(node.condicion),
                "body_actions": self._extract_actions(node.bloque),
            })
            self._extract_conditions(node.bloque, rules)

        elif isinstance(node, ast.IntentarAtraparNode):
            rules.append({
                "type": "error_handler",
                "keyword": "Intentar/Atrapar",
                "try_actions": self._extract_actions(node.bloque_intentar),
                "catch_variable": node.error_id,
                "catch_actions": self._extract_actions(node.bloque_atrapar),
            })
            self._extract_conditions(node.bloque_intentar, rules)
            self._extract_conditions(node.bloque_atrapar, rules)

        elif isinstance(node, ast.ElegirNode):
            cases = []
            for caso in node.casos:
                cases.append({
                    "value": self._serialize_expression(caso.valor),
                    "actions": self._extract_actions(caso.bloque),
                })
            rules.append({
                "type": "switch",
                "keyword": "Elegir",
                "variable": node.identificador,
                "cases": cases,
            })

        elif isinstance(node, (ast.ProgramNode, ast.BloqueNode)):
            for inst in node.instrucciones:
                self._extract_conditions(inst, rules)

    def _extract_actions(self, node: ast.ASTNode) -> List[str]:
        """Extrae descripciones textuales de acciones dentro de un bloque."""
        actions = []
        if node is None:
            return actions

        if isinstance(node, ast.BloqueNode):
            for inst in node.instrucciones:
                actions.extend(self._extract_actions(inst))
        elif isinstance(node, ast.ReglaSeguridadNode):
            parts = [node.accion]
            if node.operacion:
                parts.append(node.operacion)
            parts.append(node.identificador)
            actions.append(" ".join(parts))
        elif isinstance(node, ast.SentenciaSalidaNode):
            actions.append(f"{node.tipo_salida} {self._serialize_expression(node.valor)}")
        elif isinstance(node, ast.AsignacionRolAccionNode):
            regla = node.regla
            parts = [f"Rol {node.rol_id} =", regla.accion]
            if regla.operacion:
                parts.append(regla.operacion)
            parts.append(regla.identificador)
            actions.append(" ".join(parts))

        return actions

    def _serialize_condition(self, node: ast.ASTNode) -> str:
        """Serializa una condición del AST a formato legible."""
        if node is None:
            return ""

        if isinstance(node, ast.CondicionBinariaNode):
            izq = self._serialize_expression(node.izq)
            der = self._serialize_expression(node.der)
            return f"{izq} {node.operador} {der}"

        if isinstance(node, ast.CondicionLogicaNode):
            izq = self._serialize_condition(node.izq)
            der = self._serialize_condition(node.der)
            return f"({izq} {node.operador} {der})"

        if isinstance(node, ast.CondicionUnariaNode):
            expr = self._serialize_condition(node.expresion)
            return f"{node.operador} ({expr})"

        return self._serialize_expression(node)

    def _serialize_expression(self, node: ast.ASTNode) -> str:
        """Serializa una expresión simple a su representación textual."""
        if node is None:
            return ""
        if isinstance(node, ast.LiteralNode):
            if isinstance(node.valor, str):
                return f'"{node.valor}"'
            return str(node.valor)
        if isinstance(node, ast.IdentificadorNode):
            return node.nombre
        if isinstance(node, ast.CondicionBinariaNode):
            return self._serialize_condition(node)
        if isinstance(node, ast.CondicionLogicaNode):
            return self._serialize_condition(node)
        if isinstance(node, ast.CondicionUnariaNode):
            return self._serialize_condition(node)
        return str(node)

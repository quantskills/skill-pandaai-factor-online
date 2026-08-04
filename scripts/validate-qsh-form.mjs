#!/usr/bin/env node

import { readFile } from "node:fs/promises";

const MAX_BLOCK_BYTES = 16 * 1024;
const FIELD_TYPES = new Set(["text", "textarea", "select", "date", "number"]);
const RESERVED_KEYS = new Set(["task", "attachments"]);
const KEY_PATTERN = /^[a-z0-9_]{1,32}$/;
const FORM_PATTERN = /^```json qsh-form[ \t]*\r?\n([\s\S]*?)^```[ \t]*$/m;

function validateQshForm(source) {
  const match = FORM_PATTERN.exec(source);
  if (!match) {
    return { found: false, errors: [] };
  }

  const errors = [];
  if (Buffer.byteLength(match[0], "utf8") > MAX_BLOCK_BYTES) {
    errors.push("qsh-form 整块不能超过 16KB");
  }

  let form;
  try {
    form = JSON.parse(match[1]);
  } catch (error) {
    errors.push(`qsh-form 不是合法 JSON：${error.message}`);
    return { found: true, errors };
  }

  if (!isObject(form)) {
    errors.push("qsh-form 根节点必须是对象");
    return { found: true, errors };
  }

  if (form.version !== 1) {
    errors.push("version 必须严格等于 1");
  }

  if (form.task !== undefined) {
    if (!isObject(form.task)) {
      errors.push("task 必须是对象");
    } else {
      if (form.task.placeholder !== undefined && typeof form.task.placeholder !== "string") {
        errors.push("task.placeholder 必须是 string");
      }
      if (form.task.required !== undefined && typeof form.task.required !== "boolean") {
        errors.push("task.required 必须是 boolean");
      }
    }
  }

  const fieldKeys = new Set();
  if (form.fields !== undefined) {
    if (!Array.isArray(form.fields)) {
      errors.push("fields 必须是数组");
    } else {
      if (form.fields.length > 12) {
        errors.push("fields 最多包含 12 项");
      }
      form.fields.forEach((field, index) => {
        const path = `fields[${index}]`;
        if (!isObject(field)) {
          errors.push(`${path} 必须是对象`);
          return;
        }

        if (typeof field.key !== "string" || !KEY_PATTERN.test(field.key)) {
          errors.push(`${path}.key 必须匹配 ^[a-z0-9_]{1,32}$`);
        } else if (RESERVED_KEYS.has(field.key)) {
          errors.push(`${path}.key 不能是 task 或 attachments`);
        } else if (fieldKeys.has(field.key)) {
          errors.push(`${path}.key 不能重复：${field.key}`);
        } else {
          fieldKeys.add(field.key);
        }

        if (!FIELD_TYPES.has(field.type)) {
          errors.push(`${path}.type 必须是 text、textarea、select、date 或 number`);
        }

        if (field.type === "select") {
          if (!Array.isArray(field.options) || field.options.length === 0) {
            errors.push(`${path}.options 必须是非空数组`);
          } else {
            field.options.forEach((option, optionIndex) => {
              if (
                !isObject(option) ||
                typeof option.value !== "string" ||
                typeof option.label !== "string"
              ) {
                errors.push(`${path}.options[${optionIndex}] 必须是 {value,label} 字符串对`);
              }
            });
          }
        }
      });
    }
  }

  if (typeof form.prompt_template !== "string" || form.prompt_template.trim() === "") {
    errors.push("prompt_template 必须是非空 string");
  } else {
    const allowedVariables = new Set([...fieldKeys, ...RESERVED_KEYS]);
    const variablePattern = /{{\s*#?\s*([a-zA-Z0-9_]+)\s*}}/g;
    for (const variable of form.prompt_template.matchAll(variablePattern)) {
      if (!allowedVariables.has(variable[1])) {
        errors.push(`prompt_template 引用了未声明变量：${variable[1]}`);
      }
    }
  }

  return { found: true, errors };
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

async function main() {
  const skillPath = process.argv[2];
  if (!skillPath) {
    console.error("用法：node scripts/validate-qsh-form.mjs <SKILL.md 路径>");
    process.exitCode = 1;
    return;
  }

  let source;
  try {
    source = await readFile(skillPath, "utf8");
  } catch (error) {
    console.error(`无法读取 ${skillPath}：${error.message}`);
    process.exitCode = 1;
    return;
  }

  const result = validateQshForm(source);
  if (!result.found) {
    console.log("提示：未找到 qsh-form 块；表单声明是可选增强，校验通过。");
    return;
  }
  if (result.errors.length > 0) {
    result.errors.forEach((error) => console.error(`错误：${error}`));
    process.exitCode = 1;
    return;
  }
  console.log("qsh-form 校验通过。");
}

await main();

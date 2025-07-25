import typer
from rich import print as rprint

from stc.ontology.loader import load_ontology
from stc.emitters.jsonschema import emit_jsonschema
from stc.emitters.pydantic_models import emit_pydantic_models
from stc.emitters.ts_interfaces import emit_ts_interfaces
from stc.emitters.grammar import emit_peg_grammar
from stc.data.curate import curate_corpus
from stc.train.trainer import train_model
from stc.tests.testgen import generate_property_tests
from stc.deploy.packager import build_bundle, deploy_runtime

app = typer.Typer(help="Semantic Toolchain (stc) CLI")

# ---------- INIT ----------
@app.command()
def init(name: str = typer.Argument(..., help="Domain name (e.g. fairwork)")):
    """
    Scaffold a new domain project (folders, sample ontology file, etc.)
    """
    # TODO: copy template files, create ontology/ folder etc.
    rprint(f"[green]Initialized domain project '{name}'[/green]")

# ---------- COMPILE ----------
@app.command()
def compile(
    ontology: str = typer.Argument(..., help="Path to ontology YAML/JSON"),
    out: str = typer.Option("build/", help="Output dir"),
    emit: list[str] = typer.Option(
        ["jsonschema", "pydantic", "ts", "grammar"], help="Artifacts to emit"
    ),
):
    """
    Compile ontology into schemas, validators & grammars.
    """
    onto = load_ontology(ontology)
    if "jsonschema" in emit:
        emit_jsonschema(onto, out)
    if "pydantic" in emit:
        emit_pydantic_models(onto, out)
    if "ts" in emit:
        emit_ts_interfaces(onto, out)
    if "grammar" in emit:
        emit_peg_grammar(onto, out)
    rprint(f"[cyan]Compiled ontology → {emit} into {out}[/cyan]")

# ---------- CURATE ----------
@app.command()
def curate(
    raw_dir: str = typer.Argument(..., help="Raw data directory"),
    out: str = typer.Option("data/clean/", help="Cleaned output dir"),
    include_tags: str = typer.Option("", help="Comma-separated tags to keep"),
    exclude_tags: str = typer.Option("pii", help="Tags to drop"),
):
    """
    Filter/dedupe/annotate raw corpora into ontology-aligned datasets.
    """
    curate_corpus(raw_dir, out, include_tags.split(","), exclude_tags.split(","))
    rprint(f"[cyan]Curated data → {out}[/cyan]")

# ---------- TRAIN ----------
@app.command()
def train(
    base: str = typer.Option("mistral-0.7b", help="Base model id / path"),
    data: str = typer.Option("data/clean/train.jsonl", help="Training file"),
    schema: str = typer.Option("build/schema.json", help="JSON schema path"),
    decoder: str = typer.Option("build/grammar.peg", help="Grammar/decoder file"),
    out: str = typer.Option("models/mvm.ckpt", help="Output checkpoint path"),
    lora: bool = typer.Option(True, help="Use LoRA fine-tuning"),
    epochs: int = typer.Option(3, help="Epochs"),
):
    """
    Fine-tune a domain-specific model with schema-aware rejection sampling.
    """
    train_model(base, data, schema, decoder, out, lora, epochs)
    rprint(f"[green]Model trained → {out}[/green]")

# ---------- TESTGEN ----------
@app.command()
def testgen(
    schema: str = typer.Argument(..., help="JSON schema path"),
    out: str = typer.Option("tests/property_tests.py", help="Output test file"),
):
    """
    Generate property-based tests from ontology constraints.
    """
    generate_property_tests(schema, out)
    rprint(f"[cyan]Generated tests → {out}[/cyan]")

# ---------- DEPLOY ----------
@app.command()
def deploy(
    model: str = typer.Argument(..., help="Model checkpoint"),
    schema: str = typer.Argument(..., help="Schema JSON"),
    runtime: str = typer.Option("k8s", help="k8s|local|ecs"),
    bundle: bool = typer.Option(True, help="Create deployable bundle"),
):
    """
    Package model + validators and deploy with a fail-closed runtime.
    """
    artifact = build_bundle(model, schema) if bundle else model
    deploy_runtime(artifact, runtime)
    rprint("[green]Deployment complete[/green]")

if __name__ == "__main__":
    app() 
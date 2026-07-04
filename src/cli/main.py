import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from src.core.image_scraper import MultiEngineScraper
from src.core.dataset_scraper import DatasetScraper
from src.core.spider import SpiderScraper

console = Console()

def main():
    """
    Entry point interactivo para Scrapic - Ninja Harvester.
    Provee un menú en consola para iniciar misiones de scraping:
    Imágenes, Datasets/Audio y Rastreo Spider.
    """
    while True:
        # Header principal dividido para respetar PEP8
        title = "[bold cyan]🤖 Scrapic - Ninja Harvester[/bold cyan]"
        subtitle = "[italic]Multi-Purpose Scraper OSINT & Dataset Builder[/italic]\n[bold teal]✨ by [link=https://yeib.cl]Yeib[/link] ✨[/bold teal]"
        console.print(Panel.fit(f"{title}\n{subtitle}", border_style="cyan"))
        
        console.print("\n[bold yellow]¿Qué tipo de misión deseas iniciar?[/bold yellow]")
        console.print("1. 🖼️  Imágenes (Múltiples motores de búsqueda)")
        console.print("2. 📊  Dataset Builder (Busca archivos: .pdf, .csv, .mp3...)")
        console.print("3. 🕸️  Modo Spider (Rastrea y extrae todos los archivos de un sitio web)")
        console.print("4. ❌  Salir")
        
        modo = Prompt.ask("Elige tu misión", choices=["1", "2", "3", "4"], default="1")
        
        if modo == "4":
            console.print("[bold green]¡Hasta la próxima misión, Ninja! 🥷[/bold green]")
            break
        
        if modo == "1":
            table = Table(title="Buscadores de Imágenes", show_header=True, header_style="bold magenta")
            table.add_column("Opción", style="dim", width=12)
            table.add_column("Motores", style="cyan")
            
            table.add_row("1", "Todos (Bing, Baidu, Yandex)")
            table.add_row("2", "Solo Yandex")
            table.add_row("3", "Bing + Baidu")
            table.add_row("4", "Seleccionar uno manual")
            table.add_row("0", "[yellow]Volver al menú principal[/yellow]")
            
            console.print(table)
            
            choice = Prompt.ask("Elige una opción", choices=["0", "1", "2", "3", "4"], default="1")
            if choice == "0":
                continue
                
            selected_engines = []
            if choice == '1': selected_engines = ['bing', 'baidu', 'yandex']
            elif choice == '2': selected_engines = ['yandex']
            elif choice == '3': selected_engines = ['bing', 'baidu']
            elif choice == '4':
                sub_choice = Prompt.ask("Escribe el buscador", choices=["bing", "baidu", "yandex"], default="bing")
                selected_engines = [sub_choice]

            concepts_input = Prompt.ask("\n[bold yellow]Ingresa los conceptos separados por coma (o 'volver')[/bold yellow]")
            if concepts_input.lower() == 'volver': continue
            
            concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
            if not concepts: continue

            limit = IntPrompt.ask("[bold yellow]¿Cuántas fotos por buscador y concepto?[/bold yellow]", default=10)

            scraper = MultiEngineScraper()

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
                for concept in concepts:
                    task_id = progress.add_task(f"[cyan]Scrapeando '{concept}'...", total=len(selected_engines))
                    concept_dir = scraper.create_concept_dir(concept)
                    
                    if 'bing' in selected_engines:
                        progress.update(task_id, description=f"[cyan]Scrapeando '{concept}' en Bing...[/cyan]")
                        scraper.scrape_bing(concept, concept_dir, limit)
                        progress.advance(task_id)
                    if 'baidu' in selected_engines:
                        progress.update(task_id, description=f"[cyan]Scrapeando '{concept}' en Baidu...[/cyan]")
                        scraper.scrape_baidu(concept, concept_dir, limit)
                        progress.advance(task_id)
                    if 'yandex' in selected_engines:
                        progress.update(task_id, description=f"[cyan]Scrapeando '{concept}' en Yandex...[/cyan]")
                        scraper.scrape_yandex(concept, concept_dir, limit)
                        progress.advance(task_id)
                        
                    progress.update(task_id, description=f"[green]✓ '{concept}' finalizado.[/green]")

            console.print("\n[bold green]🎉 ¡Descarga terminada! Revisa la carpeta 'downloads/imagenes'.[/bold green]\n")
            
        elif modo == "2":
            console.print("\n[bold cyan]📊 Modo Dataset Builder (Dorking + Smart Validation)[/bold cyan]")
            
            ext_prompt = "[bold yellow]¿Qué formato buscas?[/bold yellow] (Escribe 'volver' para regresar)"
            ext_choices = [".pdf", ".csv", ".json", ".xlsx", ".md", ".mp3", "volver"]
            ext = Prompt.ask(ext_prompt, choices=ext_choices, default=".csv")
            if ext.lower() == 'volver': continue
            
            concepts_input = Prompt.ask("\n[bold yellow]Ingresa los temas a investigar separados por coma[/bold yellow]")
            concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
            if not concepts: continue

            limit = IntPrompt.ask(f"[bold yellow]¿Cuántos archivos {ext} intentar descargar por concepto?[/bold yellow]", default=5)
            
            console.print("[dim]Filtros Inteligentes: Los CSV y JSON vacíos serán destruidos automáticamente.[/dim]")
            min_size = Prompt.ask("¿Tamaño mínimo en MB? (0 para ignorar)", default="0")
            min_size_mb = float(min_size) if min_size.replace('.','',1).isdigit() else 0.0
            
            min_pages = 0
            max_duration = 15
            if ext == '.pdf':
                pages_ans = Prompt.ask("¿Páginas mínimas? (0 para ignorar)", default="0")
                min_pages = int(pages_ans) if pages_ans.isdigit() else 0
            elif ext == '.mp3':
                dur_ans = Prompt.ask("¿Duración máxima en minutos? (0 para sin límite)", default="15")
                max_duration = int(dur_ans) if dur_ans.isdigit() else 15
                console.print("[bold yellow]⚠ Atento al progreso real de descarga que aparecerá en esta consola...[/bold yellow]")
                
            scraper = DatasetScraper()
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
                for concept in concepts:
                    task_id = progress.add_task(f"[cyan]Scrapeando '{concept}'...", total=None)
                    
                    count = scraper.scrape_dataset(
                        concept, 
                        file_ext=ext, 
                        limit=limit, 
                        min_size_mb=min_size_mb, 
                        min_pages=min_pages,
                        max_duration_mins=max_duration
                    )
                    
                    if count == 0:
                        progress.update(task_id, description=f"[yellow]⚠ '{concept}' falló (nada encontrado o filtro muy estricto).[/yellow]")
                    else:
                        progress.update(task_id, description=f"[green]✓ '{concept}' finalizado ({count} archivos).[/green]")
                    
            base_folder = "audio" if ext == '.mp3' else "documentos"
            console.print(f"\n[bold green]🎉 ¡Archivos guardados! Revisa la carpeta 'downloads/{base_folder}'.[/bold green]\n")

        elif modo == "3":
            console.print("\n[bold cyan]🕸️ Modo Spider (Rastreo Recursivo)[/bold cyan]")
            start_url = Prompt.ask("[bold yellow]Ingresa la URL base a rastrear[/bold yellow] (ej: https://ejemplo.com o 'volver')")
            if start_url.lower() == 'volver': continue
            
            exts_input = Prompt.ask("[bold yellow]¿Qué extensiones extraer? (ej: .pdf, .csv, .mp3, .zip)[/bold yellow]", default=".pdf,.csv")
            target_exts = [e.strip() if e.strip().startswith('.') else f".{e.strip()}" for e in exts_input.split(",")]
            
            max_depth = IntPrompt.ask("[bold yellow]¿Profundidad máxima de clicks?[/bold yellow]", default=2)
            max_files = IntPrompt.ask("[bold yellow]¿Límite de archivos a extraer?[/bold yellow]", default=20)
            
            regex_input = Prompt.ask("[bold yellow]¿Filtrar por patrón Regex? (ej: reporte_.*)[/bold yellow] (deja en blanco para ignorar)", default="")
            regex_pattern = regex_input.strip() if regex_input.strip() else None
            
            console.print(f"\n[bold green]🚀 Soltando la Araña en {start_url}...[/bold green]\n")
            
            spider = SpiderScraper()
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task_id = progress.add_task(f"[cyan]Rastreando red y extrayendo {target_exts}...", total=None)
                spider.crawl_and_download(
                    start_url, 
                    target_extensions=target_exts, 
                    max_depth=max_depth, 
                    max_files=max_files,
                    regex_pattern=regex_pattern
                )
                progress.update(task_id, description="[green]✓ Rastreo finalizado.[/green]")
                
            console.print("\n[bold green]🎉 ¡Spider completó su misión! Revisa la carpeta 'downloads/spider'.[/bold green]\n")

if __name__ == "__main__":
    main()

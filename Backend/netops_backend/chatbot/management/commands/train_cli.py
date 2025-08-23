from django.core.management.base import BaseCommand, CommandError
from chatbot.nlp_engine.train_model import train_cli_model


class Command(BaseCommand):
    help = "Train NL->CLI translation model (stores artifacts in output directory)."

    def add_arguments(self, parser):
        parser.add_argument('--model', default='t5-small')
        parser.add_argument('--dataset', default=None, help='Path to JSON train file (defaults to nlp_engine/data/train.json)')
        parser.add_argument('--out', default='./cli_model', help='Output directory for trained model')
        parser.add_argument('--epochs', type=int, default=5)
        parser.add_argument('--batch', type=int, default=8)
        parser.add_argument('--lr', type=float, default=5e-5)
        parser.add_argument('--val-split', type=float, default=0.0, help='Fraction (0-1) for validation split; 0 disables eval')

    def handle(self, *args, **options):
        try:
            path = train_cli_model(
                model_name=options['model'],
                dataset_file=options['dataset'],
                output_dir=options['out'],
                epochs=options['epochs'],
                batch_size=options['batch'],
                learning_rate=options['lr'],
                val_split=options['val_split'],
            )
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except RuntimeError as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(f"Training complete. Model saved to {path}"))

from django.db import migrations

def criar_stp_custom_fields(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    CustomField = apps.get_model('extras', 'CustomField')
    CustomFieldChoiceSet = apps.get_model('extras', 'CustomFieldChoiceSet')

    try:
        # Obter os ContentTypes corretos de forma segura para migrações
        ct_device = ContentType.objects.get(app_label='dcim', model='device')
        ct_interface = ContentType.objects.get(app_label='dcim', model='interface')

        # ── DISPOSITIVOS (Switches) ──────────────────────────────────────
        cf_root, _ = CustomField.objects.update_or_create(
            name='stp_root_bridge',
            defaults={
                'label': 'STP Root Bridge',
                'type': 'boolean',
                'description': 'Indica se este dispositivo é o Root Bridge STP',
                'required': False,
                'default': False,
            }
        )
        # Em migrações puras, usamos .add() em vez de .set() para relações m2m históricas
        cf_root.object_types.add(ct_device)

        cf_prio, _ = CustomField.objects.update_or_create(
            name='stp_priority',
            defaults={
                'label': 'STP Priority',
                'type': 'integer',
                'description': 'Prioridade STP do dispositivo (0-61440, múltiplos de 4096)',
                'required': False,
                'default': 32768,
            }
        )
        cf_prio.object_types.add(ct_device)

        # ── CHOICE SETS ───────────────────────────────────────────────────
        choice_state, _ = CustomFieldChoiceSet.objects.update_or_create(
            name='stp_port_states',
            defaults={
                'extra_choices': [
                    ('forwarding', 'Forwarding'),
                    ('blocking', 'Blocking'),
                    ('learning', 'Learning'),
                    ('disabled', 'Disabled')
                ]
            }
        )

        choice_role, _ = CustomFieldChoiceSet.objects.update_or_create(
            name='stp_port_roles',
            defaults={
                'extra_choices': [
                    ('root', 'Root'),
                    ('designated', 'Designated'),
                    ('alternate', 'Alternate'),
                    ('disabled', 'Disabled')
                ]
            }
        )

        # ── INTERFACES ───────────────────────────────────────────────────
        cf_state, _ = CustomField.objects.update_or_create(
            name='stp_port_state',
            defaults={
                'label': 'STP Port State',
                'type': 'select',
                'description': 'Estado STP desta interface',
                'required': False,
                'default': 'forwarding',
                'choice_set': choice_state,
            }
        )
        cf_state.object_types.add(ct_interface)

        cf_role, _ = CustomField.objects.update_or_create(
            name='stp_port_role',
            defaults={
                'label': 'STP Port Role',
                'type': 'select',
                'description': 'Papel STP desta interface',
                'required': False,
                'default': 'designated',
                'choice_set': choice_role,
            }
        )
        cf_role.object_types.add(ct_interface)

        print("✅ [STP] Custom Fields criados com sucesso na migração!")
    except Exception as e:
        print(f"⚠️ [STP] Erro ao aplicar migração: {e}")
        raise e  # Força o Django a lançar a exceção se algo falhar a sério

def revogar_custom_fields(apps, schema_editor):
    CustomField = apps.get_model('extras', 'CustomField')
    CustomField.objects.filter(name__in=['stp_root_bridge', 'stp_priority', 'stp_port_state', 'stp_port_role']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('dcim', '0001_initial'), 
        ('extras', '0001_initial'),
        ('netbox_topology_vlan', '0001_initial'), # Garante que corre DEPOIS da tua primeira migração
    ]

    operations = [
        migrations.RunPython(criar_stp_custom_fields, revogar_custom_fields),
    ]
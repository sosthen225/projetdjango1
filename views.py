from datetime import timezone
from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from appFinal.form import CarnetForm, ConsultationForm, DiagnosticForm, DiagnosticFormSet, InfirmierLoginForm, InfirmierSignUpForm, MedecinLoginForm, MedecinSignUpForm, PatientForm, TraitementForm, TraitementFormSet
from appFinal.models import Carnet, Consultation, Diagnostic, Infirmier, Medecin, Patient, Traitement
# Create your views here.



def login(request):
    form_medecin = MedecinLoginForm()
    form_infirmier = InfirmierLoginForm()

    if request.method == 'POST':
        # Choisissez le formulaire en fonction du type d'utilisateur (médecin ou infirmier)
        if 'medecin_login' in request.POST:
            form_medecin = MedecinLoginForm(request.POST)
            form = form_medecin
        elif 'infirmier_login' in request.POST:
            form_infirmier = InfirmierLoginForm(request.POST)
            form = form_infirmier
        else:
            form = None

        if form and form.is_valid():
            user = form.get_user()
            if user is not None:
                auth_login(request, user)
                if 'medecin_login' in request.POST:
                    return redirect('medecin_dashboard')
                elif 'infirmier_login' in request.POST:
                    return redirect('infirmier_dashboard')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'login.html', {
        'form_medecin': form_medecin,
        'form_infirmier': form_infirmier
    })
 


@login_required
def accueil_infirmier(request):

 infirmier = Infirmier.objects.get(user=request.user)
 return render(request, 'infirmier_dashboard.html', {'medecin': infirmier})



def nouveau_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.infirmier = request.user.infirmier
            patient.save()
            
            messages.success(request, 'Nouveau patient enregistré avec succès.')
            return redirect('nouveau_carnet')
    else:
        form = PatientForm()
    return render(request, 'nouveau_patient.html', {'form': form})




def nouveau_carnet(request):
    if request.method == 'POST':
        form = CarnetForm(request.POST)
        if form.is_valid():
            carnet = form.save(commit=False)
            
            # Récupérez l'ID du patient à partir du formulaire POST
            patient_id = request.POST.get('patient')
            print (request.POST)
            # Assurez-vous que l'infirmier a accès à ce patient
            try:
                carnet.patient = request.user.infirmier.patient_set.get(id=patient_id)
            except Patient.DoesNotExist:
                messages.error(request, "Le patient sélectionné n'existe pas ou n'est pas accessible pour cet infirmier.")
                return redirect('nouveau_carnet')  # Rediriger vers la même page ou une autre vue appropriée
            
            carnet.save()

            messages.success(request, "Carnet ajouté avec succès.")
            return redirect('liste_patients')
    else:
        form = CarnetForm()
    return render(request, 'nouveau_carnet.html', {'form': form})



def liste_patients(request):
    
    patients = Patient.objects.all()
    patients = Patient.objects.order_by('nom')
    return render(request, 'liste_patients.html', {'patients': patients})


def voir_carnet(request, patient_id):
    carnet = get_object_or_404(Carnet, patient_id=patient_id)
    return render(request, 'voir_carnet.html', {'carnet': carnet})


def modifier_carnet(request, patient_id):
    carnet = get_object_or_404(Carnet, patient_id=patient_id)
    if request.method == 'POST':
        form = CarnetForm(request.POST, instance=carnet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Carnet modifié avec succès.')
            return redirect('liste_patients')
    else:
        form = CarnetForm(instance=carnet)
    return render(request, 'modifier_carnet.html', {'form': form})



@login_required
def accueil_medecin(request):
 
 medecin = Medecin.objects.get(user=request.user)
 return render(request, 'medecin_dashboard.html', {'medecin': medecin})
     
 
def infirmier_signup(request):
   if request.method == 'POST':
        form = InfirmierSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscription réussie ! Vous pouvez maintenant vous connecter.')
            return redirect('login')  # Rediriger vers la page de connexion après inscription
   else:
        form = InfirmierSignUpForm()
   return render(request, 'signup.html', {'form': form})



def medecin_signup(request):
    if request.method == 'POST':
        form = MedecinSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscription réussie ! Vous pouvez maintenant vous connecter.')
            return redirect('login')  # Rediriger vers la page de connexion après inscription
    else:
        form = MedecinSignUpForm()
    return render(request, 'signup.html', {'form': form})





def rechercher_patient(request):
    code_patient = request.GET.get('code_patient')

    if not code_patient:
        messages.error(request, "Veuillez saisir un code patient pour effectuer la recherche.")
        return render(request, 'entrez_code.html')

    try:
        patient = Patient.objects.get(code_patient=code_patient)
    except Patient.DoesNotExist:
        messages.error(request, "Aucun patient trouvé avec le code fourni.")
        return render(request, 'entrez_code.html')

    return render(request, 'patient_trouvé.html', {'patient': patient})

        





def nouveau_diagnostic(request,patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    consultation_form = ConsultationForm(initial={'patient': patient, 'medecin': request.user.medecin})
    diagnostic_form = DiagnosticForm()
    traitement_form = TraitementForm()

    if request.method == 'POST':
        consultation_form = ConsultationForm(request.POST, initial={'patient': patient, 'medecin': request.user.medecin})
        diagnostic_form = DiagnosticForm(request.POST)
        traitement_form = TraitementForm(request.POST)

        if consultation_form.is_valid() and diagnostic_form.is_valid() and traitement_form.is_valid():
          today = timezone.now().date()
          consultation = Consultation.objects.filter(
          patient=patient,
          medecin=request.user.medecin,
          date_consultation__date=today
          ).first()
    
        if not consultation:
            consultation = consultation_form.save(commit=False)
            consultation.patient = patient
            consultation.medecin = request.user.medecin
            consultation.save()

            diagnostic = diagnostic_form.save(commit=False)
            diagnostic.consultation = consultation
            diagnostic.save()

            traitement = traitement_form.save(commit=False)
            traitement.diagnostic = diagnostic
            traitement.save()

            return redirect('patient_trouvé.html', patient_id=patient.id)

    return render(request, 'diagno.html', {
        'patient': patient,
        'consultation_form': consultation_form,
        'diagnostic_form': diagnostic_form,
        'traitement_form': traitement_form
    })


"""
if request.method == 'POST':
                consultation_form = ConsultationForm(request.POST)
                diagnostic_formset = DiagnosticFormSet(request.POST, queryset=Diagnostic.objects.none())
                traitement_formset = TraitementFormSet(request.POST, queryset=Traitement.objects.none())

                if consultation_form.is_valid() and diagnostic_formset.is_valid() and traitement_formset.is_valid():
                    for consultation in consultation:
                        consultation = consultation_form.save(commit=False)
                        consultation.patient = patient
                        consultation.medecin = request.user
                        consultation.save()
                    
                    for form in diagnostic_formset:
                        diagnostic = form.save(commit=False)
                        diagnostic.consultation = consultation
                        diagnostic.save()

                    for form in traitement_formset:
                        traitement = form.save(commit=False)
                        traitement.diagnostic = diagnostic
                        traitement.save()

                    messages.success(request, 'Diagnostic et traitement ajoutés avec succès.')
                    return redirect(reverse('entrez_code') + f'?code_patient={patient.code_patient}')

"""








'''

def register_consultation(request):
    if request.method == 'POST':
        consultation_form = ConsultationForm(request.POST)
        diagnostic_forms = DiagnosticFormSet(request.POST, prefix='diagnostic')
        traitement_forms = TraitementFormSet(request.POST, prefix='traitement')

        if consultation_form.is_valid() and diagnostic_forms.is_valid() and traitement_forms.is_valid():
            consultation = consultation_form.save(commit=False)
            consultation.medecin = request.user
            consultation.save()

            for diagnostic_form in diagnostic_forms:
                diagnostic = diagnostic_form.save(commit=False)
                diagnostic.consultation = consultation
                diagnostic.save()

                for traitement_form in traitement_forms:
                    traitement = traitement_form.save(commit=False)
                    traitement.diagnostic = diagnostic
                    traitement.save()

            return redirect('consultation_list')

    else:
        consultation_form = ConsultationForm()
        diagnostic_forms = DiagnosticFormSet(prefix='diagnostic')
        traitement_forms = TraitementFormSet(prefix='traitement')

    return render(request, 'register_consultation.html', {
        'consultation_form': consultation_form,
        'diagnostic_forms': diagnostic_forms,
        'traitement_forms': traitement_forms
    })

'''

def consultation_list(request):
      # Récupérer l'utilisateur connecté
    utilisateur = request.user

    # Vérifier si l'utilisateur est authentifié et s'il est un médecin
    if not utilisateur.is_authenticated or not hasattr(utilisateur, 'medecin'):
        return render(request, 'login')  # Redirection vers une page non autorisée

    # Récupérer l'objet médecin
    medecin = utilisateur.medecin

    # Filtrer les consultations en fonction du médecin
    consultations = Consultation.objects.filter(medecin=medecin)

    # Obtenir les patients associés
    patients = []
    for consultation in consultations:
        patient = consultation.patient
        if patient not in patients:
            patients.append(patient)

    # Rendre le template avec la liste des patients et les informations du médecin
    contexte = {
        'patients': patients,
        'medecin': medecin,
    }
    return render(request, 'consultation_list.html', contexte)
    ''' # Récupérer l'ID du médecin connecté
    doctor_id = request.user.id

    # Filtrer les consultations en fonction de l'ID du médecin
    consultations = Consultation.objects.filter(doctor_id=doctor_id)

    # Obtenir les patients associés
    patients = []
    for consultation in consultations:
        patient = consultation.patient
        if patient not in patients:
            patients.append(patient)

    # Rendre le template avec la liste des patients
    context = {
        'patients': patients
    }
    return render(request, 'consultation_list.html', context)
    return render(request,'consultation_list.html')'''











def logout_view(request):
    request.session.flush()
    return redirect('login')
from flask import Flask, json, abort, request, jsonify
from groq import Groq
import os
from crew import DreamAnalysisCrew
from threading import Thread
from uuid import uuid4
from inMemoryStore import SingletonInMemoryEvents, Event
from flask_cors import CORS, cross_origin
from db import SingleDb
from functools import wraps


app = Flask('dreamAgent')
CORS(app)
def kickoffCrew(jobId:str, dream:str):
    inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
    res = None
    try:
        dreamAnalysisCrew = DreamAnalysisCrew(jobId)
        dreamAnalysisCrew.setup_crew(dream)
        res = dreamAnalysisCrew.kickoff()
    except Exception as e:
        inMemoryStore.appendEvent(jobId, 'event crew kickoff failed')
        inMemoryStore.updateJobStatus(jobId, 'ERROR')
        inMemoryStore.updateJobAnalysisSummary(jobId, str(e))
        print(str(e))
        return {"status":"failed"}
    print("@#################################", res, type(res))
    inMemoryStore.updateJobStatus(jobId, 'COMPLETE')
    inMemoryStore.updateJobAnalysisSummary(jobId, res)
    inMemoryStore.appendEvent(jobId, 'COMPLETE')
    print(jobId)

def kickoffCrewPremium(jobId:str, dream:str):
    inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
    res = None
    try:
        dreamAnalysisCrew = DreamAnalysisCrew(jobId, 'chatgpt')
        dreamAnalysisCrew.setup_crew(dream)
        res = dreamAnalysisCrew.kickoff()
    except Exception as e:
        inMemoryStore.appendEvent(jobId, 'event crew kickoff failed')
        inMemoryStore.updateJobStatus(jobId, 'ERROR')
        inMemoryStore.updateJobAnalysisSummary(jobId, str(e))
        print(str(e))
        return {"status":"failed"}
    print("@#################################", res, type(res))
    inMemoryStore.updateJobStatus(jobId, 'COMPLETE')
    inMemoryStore.updateJobAnalysisSummary(jobId, res)
    inMemoryStore.appendEvent(jobId, 'COMPLETE')
    print(jobId)

def authDecoParams(reqType='GET'):
    def authDecorator(func):
        print("lmaolmaolmaolmao",reqType)
        @wraps(func)
        def decorator(*args, **kwargs):
            if reqType=='GET':
                userId = request.args.get('req')
            elif reqType=='POST':
                reqData = request.json
                if not 'currentUserId' in reqData:
                    return {"status":"unauthorized"}
                userId = reqData['currentUserId']
            else:
                return {"status":"invalid_method"}
            print(userId)
            supabase = SingleDb.getInstance()
            res = supabase.table('UserTier').select('tier').filter('clerkId', 'eq', userId).execute()
            print("#############################",res)
            try:
                data = res.data
                if data and data[0]['tier']!='admin':
                    return {"status":"unauthorized"}
                return func(*args, **kwargs)
            except:
                return {'status':'auth_err'}
        return decorator
    return authDecorator

@app.route('/api/startsuperanalysis', methods=['POST'])
@authDecoParams('POST')
def startSuperAnalysis():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    dream = data['dreamWithContext']
    jobId = str(uuid4())
    t = Thread(target=kickoffCrew, args=(jobId, dream))
    try:
        t.start()
    except Exception as e:
        print(str(e))
        return {"status":"failed"}
    return jsonify({'jobId':jobId})

@app.route('/api/startanalysis', methods=['POST'])
def startAnalysis():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    dream = data['dreamWithContext']
    jobId = str(uuid4())
    t = Thread(target=kickoffCrewPremium, args=(jobId, dream))
    try:
        t.start()
    except Exception as e:
        print(str(e))
        return {"status":"failed"}
    return jsonify({'jobId':jobId})


@app.route('/api/dream/<jobId>', methods = ['GET'])
def getDreamEventsByJobId(jobId):
    inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
    lock = inMemoryStore.getLock()
    job = inMemoryStore.getJob(jobId)
    if not job:
        abort(404, description="job doesnt exist")
    try:
        result = str(job.analysisSummary)
    except:
        result = ''
    return jsonify({
        'jobId':jobId,
        'status':job.status,
        'raw':job.rawAnalysis,
        'analysis':result,
        'events':[{"timestamp":event.timestamp.isoformat(), "data":event.data} for event in job.events]
    })

@app.route('/groqdream', methods=['POST'])
def groqDream():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    res = kickoffCrew(data['dreamWithContext'])
    print("@@@@@@@@@@@@@@@@@@@", res)
    return res



@app.route('/getDreamWithContext', methods=['POST'])
def getDream():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    obj =             {
                "role": "user",
                "content": f'''only extract the jungian symbols and dont do anything else from the following dream: {data['dreamWithContext']}''',
            }
    chat_completion = client.chat.completions.create(
        messages=[
obj
        ],
        model="mixtral-8x7b-32768",
    )
    print(obj)
    return {"analysis":chat_completion.choices[0].message.content}

if __name__=='__main__':
    app.run(debug=True, port=8000)
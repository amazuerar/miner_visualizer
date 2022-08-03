import firebase from 'firebase/compat/app';
import 'firebase/compat/firestore';
import 'firebase/compat/storage';
import { auth } from '../../../assets/api_key/auth'

const firebaseInterfaces = (() => {
    firebase.initializeApp({
        apiKey: auth.apiKey,
        authDomain: auth.authDomain,
        projectId: auth.projectId,
        storageBucket: auth.storageBucket,
        messagingSenderId: auth.messagingSenderId,
        appId: auth.appId 
    });

    const firestoreDb = firebase.firestore();
    const storageRef = firebase.storage();

    return {
        firestore: 
        {
            firestoreWordsCollection: firestoreDb.collection('words')
        },
        storage: storageRef,
    };
})();

export const firestoreWords = firebaseInterfaces.firestore.firestoreWordsCollection;
